//! Offline client-code hints. No network and no claim that a route is deployed.
use regex::Regex;
use serde_json::{json, Value};
use std::collections::BTreeSet;

pub struct Rules {
    literal: Regex,
    fetch: Regex,
    method: Regex,
    client: Regex,
    prefix: Regex,
    field: Regex,
    query: Regex,
}

impl Rules {
    pub fn new() -> Self {
        Self {
            literal: Regex::new(r#"["'`]((?:https?://[^/"'`\s<>]{1,120})?/(?:api|graphql|wp-json)(?:[/ ?][^"'`\s<>]{0,400})?)["'`]"#).unwrap(),
            fetch: Regex::new(r#"\bfetch\(\s*["'`]((?:https?://|/)[^"'`\s<>]{1,512})["'`]\s*(?:,\s*(\{[^{}]{0,400}\})\s*)?\)"#).unwrap(),
            method: Regex::new(r#"\bmethod\s*:\s*["'](GET|HEAD|POST|PUT|PATCH|DELETE|OPTIONS)["']"#).unwrap(),
            client: Regex::new(r#"\b([A-Za-z_$][\w$]*)\.(get|head|post|put|patch|delete|options)\(\s*["'`]([A-Za-z0-9_/$][^"'`\s<>]{0,511})["'`]"#).unwrap(),
            prefix: Regex::new(r#"\b([A-Za-z_$][\w$]*)\s*=\s*[A-Za-z_$][\w$]*\.create\(\s*\{\s*(?:prefixUrl|baseURL)\s*:\s*["'](https?://[^"'\s<>]{1,512})["']"#).unwrap(),
            field: Regex::new(r#"\.append\(\s*["']([A-Za-z_][A-Za-z0-9_.-]{0,79})["']\s*,"#).unwrap(),
            query: Regex::new(r"(?:[?&])([A-Za-z_][A-Za-z0-9_.-]{0,79})=").unwrap(),
        }
    }

    fn route(&self, raw: &str) -> (String, Vec<String>) {
        let path = raw.split(['?', '#']).next().unwrap_or(raw).to_string();
        let mut keys: Vec<String> = self
            .query
            .captures_iter(raw)
            .map(|c| c[1].to_string())
            .collect();
        keys.sort();
        keys.dedup();
        (path, keys)
    }

    pub fn review(&self, body: &str) -> Value {
        let mut hints = Vec::new();
        let mut seen = BTreeSet::new();
        let mut truncated = false;
        let known_client_names: BTreeSet<String> = self
            .prefix
            .captures_iter(body)
            .take(200)
            .map(|c| c[1].to_string())
            .collect();
        // A call is stronger provenance than a string, but is still only client code.
        for cap in self.fetch.captures_iter(body).take(2001) {
            if hints.len() >= 2000 {
                truncated = true;
                break;
            }
            let raw = cap.get(1).unwrap();
            let method = match cap.get(2) {
                None => Some("GET".to_string()),
                Some(options) => self
                    .method
                    .captures(options.as_str())
                    .map(|c| c[1].to_string()),
            };
            let (route, keys) = self.route(raw.as_str());
            seen.insert((route.clone(), keys.clone()));
            hints.push(json!({"route":route,"method":method,"query_keys":keys,
                "byte_offset":raw.start(),"evidence":"fetch_literal","dynamic_template":raw.as_str().contains("${")}));
        }
        for cap in self.client.captures_iter(body).take(2001) {
            if hints.len() >= 2000 {
                truncated = true;
                break;
            }
            let raw = cap.get(3).unwrap();
            let method = cap[2].to_ascii_uppercase();
            let (route, keys) = self.route(raw.as_str());
            let relative = !route.starts_with('/') && !route.starts_with("http");
            if relative && !known_client_names.contains(&cap[1]) {
                continue;
            }
            seen.insert((route.clone(), keys.clone()));
            hints.push(json!({"route":route,"method":method,"query_keys":keys,
                "byte_offset":raw.start(),"evidence":"method_named_client_call","client_identifier":&cap[1],
                "relative_to_client_prefix":relative,
                "dynamic_template":raw.as_str().contains("${")}));
        }
        for (index, cap) in self.literal.captures_iter(body).take(10001).enumerate() {
            if hints.len() >= 2000 || index == 10000 {
                truncated = true;
                break;
            }
            let raw = cap.get(1).unwrap();
            let (route, keys) = self.route(raw.as_str());
            if !seen.insert((route.clone(), keys.clone())) {
                continue;
            }
            hints.push(json!({"route":route,"method":null,"query_keys":keys,
                "byte_offset":raw.start(),"evidence":"api_literal_only",
                "dynamic_template":raw.as_str().contains("${")}));
        }
        let fields: BTreeSet<String> = self
            .field
            .captures_iter(body)
            .take(2000)
            .map(|c| c[1].to_string())
            .collect();
        let prefixes: Vec<Value> = self.prefix.captures_iter(body).take(200).map(|c| {
            let raw = c.get(2).unwrap();
            json!({"client_identifier":&c[1],"prefix":self.route(raw.as_str()).0,"byte_offset":raw.start(),
                "evidence":"client_constructor_literal_not_lexically_resolved"})
        }).collect();
        json!({"hints":hints,"client_prefix_candidates":prefixes,"form_data_field_names":fields,"truncated":truncated,
            "interpretation":"client_code_only_not_live_route_or_vulnerability",
            "limits":"static literal calls; no AST, concatenated URL, lexical scope or wrapper resolution; no cross-call field association"})
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn explicit_calls_keep_methods_offsets_and_redact_query_values() {
        let body = "// żółw 🐢\nfetch('/api/read?token=DO_NOT_COPY'); fetch('/api/send',{method:'POST',body:data}); api.patch('/profile'); data.append('file',f);";
        let out = Rules::new().review(body);
        assert_eq!(out["hints"][0]["method"], "GET");
        assert_eq!(out["hints"][0]["query_keys"], json!(["token"]));
        assert_eq!(out["hints"][1]["method"], "POST");
        assert_eq!(out["hints"][2]["method"], "PATCH");
        let offset = out["hints"][0]["byte_offset"].as_u64().unwrap() as usize;
        assert!(body[offset..].starts_with("/api/read"));
        assert!(!out.to_string().contains("DO_NOT_COPY"));
        assert_eq!(out["form_data_field_names"], json!(["file"]));
    }

    #[test]
    fn does_not_guess_method_from_neighbour_or_dynamic_options() {
        let body = "const unrelated={method:'DELETE'}; const x='/api/unknown'; fetch('/api/options',{...options}); fetch('/api/nested',{body:{method:'POST'}});";
        let out = Rules::new().review(body);
        assert!(out["hints"]
            .as_array()
            .unwrap()
            .iter()
            .all(|x| x["method"].is_null()));
    }

    #[test]
    fn api_literals_are_not_lost_after_large_vendor_noise() {
        let body = "'/static/vendor.js';".repeat(4000) + "const path='/api/real';";
        let out = Rules::new().review(&body);
        assert_eq!(out["hints"][0]["route"], "/api/real");
        assert_eq!(out["hints"][0]["evidence"], "api_literal_only");
    }

    #[test]
    fn relative_client_routes_are_preserved_without_guessing_a_base() {
        let out = Rules::new().review("const api=ky.create({prefixUrl:'https://a.invalid/api/v1'}); api.get(`projects/${id}`); api.post('items',{json:data});");
        assert_eq!(out["hints"][0]["route"], "projects/${id}");
        assert_eq!(out["hints"][0]["relative_to_client_prefix"], true);
        assert_eq!(out["hints"][0]["client_identifier"], "api");
        assert_eq!(
            out["client_prefix_candidates"][0]["prefix"],
            "https://a.invalid/api/v1"
        );
        assert_eq!(out["hints"][1]["method"], "POST");
        assert_eq!(out["hints"][1]["route"], "items");
        assert!(
            Rules::new().review("headers.get('Content-Type'); cache.get('local-key');")["hints"]
                .as_array()
                .unwrap()
                .is_empty()
        );
    }
}
