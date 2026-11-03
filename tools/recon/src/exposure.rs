//! Conservative format checks on bounded captures; never follows links or uses secrets.
use regex::Regex;
use serde_json::{json, Value};

fn normalized(doc: &Value) -> String {
    let body = doc["body"].as_str().unwrap_or("");
    let path = doc["request_path"].as_str().unwrap_or("");
    let text = if path.is_empty() {
        body.to_string()
    } else {
        body.replace(path, "<PATH>")
    };
    Regex::new(r"(?i)\b[0-9a-f]{16,}\b")
        .unwrap()
        .replace_all(&text, "<HEX>")
        .into_owned()
}

pub fn review(doc: &Value, documents: &[Value]) -> Value {
    let check = doc["check"].as_str().unwrap_or("");
    if !matches!(check, "git-head" | "environment") {
        return Value::Null;
    }
    let result = |verdict: &str, reason: &str| {
        json!({"schema_version":1,"check":check,
        "verdict":verdict,"reason":reason,"confirmed":false})
    };
    if doc["status"] != 200 || !doc["error"].is_null() || doc["truncated"] == true {
        return result("inconclusive", "non_200_error_or_truncated");
    }
    let controls: Vec<_> = documents
        .iter()
        .filter(|d| {
            d["origin"] == doc["origin"]
                && matches!(d["check"].as_str(), Some("control-a" | "control-b"))
        })
        .collect();
    if controls.len() != 2
        || controls.iter().any(|c| {
            !c["error"].is_null()
                || c["truncated"] == true
                || !matches!(c["status"].as_u64(), Some(200 | 404))
        })
    {
        return result("inconclusive", "two_valid_controls_required");
    }
    let body = doc["body"].as_str().unwrap_or("").trim();
    let lower = body.to_ascii_lowercase();
    if body.starts_with('<') || lower.contains("<html") || lower.contains("<!doctype") {
        return result("negative", "html_is_not_file_evidence");
    }
    let comparable = normalized(doc);
    if controls
        .iter()
        .any(|control| normalized(control) == comparable)
    {
        return result("negative", "matches_nonexistent_path_control");
    }
    let signature = if check == "git-head" {
        body.len() <= 256
            && Regex::new(
                r"^(?:ref: refs/(?:heads|tags)/[A-Za-z0-9._/-]+|[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$",
            )
            .unwrap()
            .is_match(body)
    } else {
        // Only names and counts are inspected. Values are never included in the verdict.
        let assignment = Regex::new(r"^(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*.+$").unwrap();
        let keys: Vec<_> = body
            .lines()
            .filter_map(|line| assignment.captures(line.trim()))
            .filter_map(|capture| capture.get(1).map(|m| m.as_str().to_string()))
            .collect();
        let sensitive_name = keys.iter().any(|key| {
            [
                "PASSWORD",
                "SECRET",
                "PRIVATE_KEY",
                "API_KEY",
                "DATABASE_URL",
                "ACCESS_TOKEN",
            ]
            .iter()
            .any(|marker| key.contains(marker))
        });
        keys.len() >= 2 && sensitive_name
    };
    if signature {
        result(
            "candidate_requires_manual_impact_review",
            "file_format_differs_from_both_controls",
        )
    } else {
        result("negative", "no_strong_file_signature")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn capture(check: &str, path: &str, body: &str) -> Value {
        json!({"origin":"https://fixture.invalid","check":check,"request_path":path,
            "body":body,"status":200,"error":null,"truncated":false})
    }
    fn controls() -> Vec<Value> {
        vec![
            capture("control-a", "/missing-a", "not found /missing-a"),
            capture("control-b", "/missing-b", "not found /missing-b"),
        ]
    }
    #[test]
    fn git_signature_requires_two_controls_and_is_only_a_candidate() {
        let doc = capture("git-head", "/.git/HEAD", "ref: refs/heads/main\n");
        assert_eq!(review(&doc, &[])["verdict"], "inconclusive");
        let result = review(&doc, &controls());
        assert_eq!(result["verdict"], "candidate_requires_manual_impact_review");
        assert_eq!(result["confirmed"], false);
    }
    #[test]
    fn reflected_catch_all_and_html_never_become_file_findings() {
        let doc = capture("git-head", "/.git/HEAD", "not found /.git/HEAD");
        assert_eq!(
            review(&doc, &controls())["reason"],
            "matches_nonexistent_path_control"
        );
        let doc = capture("environment", "/.env", "<html>DB_PASSWORD=fixture</html>");
        assert_eq!(review(&doc, &controls())["verdict"], "negative");
    }
    #[test]
    fn env_hint_needs_structure_and_never_echoes_values() {
        let doc = capture(
            "environment",
            "/.env",
            "APP_NAME=fixture\nDB_PASSWORD=synthetic-value-123\n",
        );
        let result = review(&doc, &controls());
        assert_eq!(result["verdict"], "candidate_requires_manual_impact_review");
        assert!(!result.to_string().contains("synthetic-value-123"));
        let mut cut = doc.clone();
        cut["truncated"] = json!(true);
        assert_eq!(review(&cut, &controls())["verdict"], "inconclusive");
    }
}
