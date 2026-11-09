# Llama system rendering clarification

UTC 2026-11-09T08:58:47.113899+00:00. Original docs227_SYSTEM_PROMPTS.txt is unchanged. The custom A/B body follows the tokenizer's default knowledge/date header, inside the same system segment. It does not replace that header, and it is not an additional system role appended after a separately rendered default system message. The user segment is unchanged. All4000 input-ID hashes match the original2000x2 rendering audit.

Header SHA256: e9e2bfabd879275c20bc7f104bb24fae89da34bb9ec1fe4a8adeb3f52e799fda
A effective system-segment SHA256: f532fb4f317fbab57671c4d44a6fe5c500856cbccbb15dfcb9e84b9490e4f115
B effective system-segment SHA256: a461fe9242b82ced9535acea77211c2e2647471ff8715e9fee794889bfcf73b1
A body SHA256: d33c70fdd0c40dc6d2b38a6be972bb8806bd5ac174db361930bb85341be974c3
B body SHA256: 3606acab20daf5f70bde6b186c9b498ada1b0de51e4b67dd4a81a1e1745c4957

Public A/B uses the matched batch8/120token path; harmful A/B uses the single-row/2400token path. Do not pool them into a single refusal rate. Hook-count versus nonzero-injection fields retain their documented meanings. Render audit SHA256 a78163ea4aad55636dd2685c11715529de7e8f444402b5a7cca39dc51fe7a5ec.
