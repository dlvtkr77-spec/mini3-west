// Vercel 서버 함수: 조건에 맞는 후보(최대 5개) 중 하나를 Gemini로 추천받는다.
// GEMINI_API_KEY는 여기(서버)에서만 읽고, 브라우저로 돌려주거나 로그로 남기지 않는다.
// 호출 방식은 공식 문서 기준: https://ai.google.dev/api/generate-content (models.generateContent)
// 모델 목록: https://ai.google.dev/gemini-api/docs/models

// 사용할 Gemini 모델 (공식 모델 목록의 안정 버전, 빠르고 저렴한 Flash-Lite)
const MODEL = "gemini-3.5-flash-lite";
// generateContent 엔드포인트 주소
const ENDPOINT = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`;
// Gemini 응답을 기다리는 최대 시간 (밀리초)
const TIMEOUT_MS = 20000;
// 한 번에 넘길 수 있는 최대 후보 수
const MAX_CANDIDATES = 5;
// 화면에서 고를 수 있는 시즌 값 (빈 값은 조건 없음)
const SEASONS = ["", "1990", "1991", "1992"];

// AI가 지켜야 할 규칙
const SYSTEM_PROMPT = [
  "너는 사용자가 준 후보 표에서 팀-시즌 기록 하나만 고르는 도우미다.",
  "규칙:",
  "1. name과 year는 후보 표에 있는 값을 글자 그대로 복사한다.",
  "2. 같은 name이라도 year가 다르면 서로 다른 후보다.",
  "3. reasons는 정확히 2개의 한국어 문장이고, 각 문장은 줄바꿈 없는 한 줄이다.",
  "4. 첫째 문장에는 고른 후보의 wins 숫자를, 둘째 문장에는 고른 후보의 goals_for 숫자를 쓴다.",
  "5. 이유에는 고른 후보의 wins와 goals_for 숫자만 쓴다. 연도, 순위, 차이, 평균, 다른 후보의 숫자 등 다른 숫자는 쓰지 않는다.",
  "6. 후보 표 밖의 팀이나 시즌, 선수, 경기 내용, 인기, 현재 성적, 우승 가능성 등 표에 없는 정보는 말하지 않는다.",
].join("\n");

// Gemini에게 요구할 응답 모양 (JSON)
const RESPONSE_SCHEMA = {
  type: "OBJECT",
  properties: {
    name: { type: "STRING" },
    year: { type: "STRING" },
    reasons: { type: "ARRAY", items: { type: "STRING" } },
  },
  required: ["name", "year", "reasons"],
  propertyOrdering: ["name", "year", "reasons"],
};

// 정수인지 확인한다
function isInt(value) {
  return typeof value === "number" && Number.isInteger(value);
}

// 요청 본문을 검사하고, 문제가 있으면 이유 문자열을, 없으면 null을 돌려준다
function validateInput(body) {
  if (!body || typeof body !== "object") return "본문이 JSON 객체가 아닙니다.";
  const { season, minWins, candidates } = body;
  if (typeof season !== "string" || !SEASONS.includes(season)) return "season 값이 올바르지 않습니다.";
  if (minWins !== null && !(typeof minWins === "number" && Number.isFinite(minWins))) return "minWins는 null 또는 숫자여야 합니다.";
  if (!Array.isArray(candidates)) return "candidates는 배열이어야 합니다.";
  if (candidates.length < 1 || candidates.length > MAX_CANDIDATES) return `candidates는 1~${MAX_CANDIDATES}개여야 합니다.`;
  const seen = new Set();
  for (const c of candidates) {
    if (!c || typeof c !== "object") return "후보가 객체가 아닙니다.";
    if (typeof c.name !== "string" || c.name.trim() === "" || c.name.length > 100) return "후보 name이 올바르지 않습니다.";
    if (typeof c.year !== "string" || !/^\d{4}$/.test(c.year)) return "후보 year가 올바르지 않습니다.";
    if (!isInt(c.wins) || c.wins < 0) return "후보 wins가 올바르지 않습니다.";
    if (!isInt(c.goals_for) || c.goals_for < 0) return "후보 goals_for가 올바르지 않습니다.";
    // 후보가 넘겨준 조건을 실제로 만족하는지 확인한다
    if (season !== "" && c.year !== season) return "조건의 시즌과 맞지 않는 후보가 있습니다.";
    if (minWins !== null && c.wins < minWins) return "최소 승리 수보다 낮은 후보가 있습니다.";
    // 같은 name·year 조합이 두 번 들어오지 않았는지 확인한다
    const key = c.name + "|" + c.year;
    if (seen.has(key)) return "같은 name·year 후보가 중복되었습니다.";
    seen.add(key);
  }
  return null;
}

// Gemini 응답을 검사해 통과하면 {name, year, reasons}를, 아니면 null을 돌려준다
function verifyOutput(parsed, candidates) {
  if (!parsed || typeof parsed !== "object") return null;
  const { name, year, reasons } = parsed;
  if (typeof name !== "string" || typeof year !== "string") return null;
  // name과 year 조합이 넘겨준 후보 안에 있어야 한다
  const picked = candidates.find((c) => c.name === name && c.year === year);
  if (!picked) return null;
  // 이유는 정확히 두 줄이어야 한다
  if (!Array.isArray(reasons) || reasons.length !== 2) return null;
  if (!reasons.every((r) => typeof r === "string" && r.trim() !== "" && !/[\r\n]/.test(r))) return null;
  // 이유에 나온 숫자는 모두 고른 후보의 wins 또는 goals_for여야 하고, 두 값이 모두 나와야 한다
  const allowed = new Set([String(picked.wins), String(picked.goals_for)]);
  const numbers = reasons.join(" ").match(/\d+(?:[.,]\d+)*/g) || [];
  if (!numbers.every((n) => allowed.has(n))) return null;
  if (!numbers.includes(String(picked.wins)) || !numbers.includes(String(picked.goals_for))) return null;
  return { name: picked.name, year: picked.year, reasons: reasons.map((r) => r.trim()) };
}

// Vercel Node.js 서버 함수 진입점
module.exports = async function handler(req, res) {
  // POST 요청만 받는다
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "method_not_allowed" });
  }

  // 본문이 문자열로 오면 JSON으로 바꾼다
  let body = req.body;
  if (typeof body === "string") {
    try {
      body = JSON.parse(body);
    } catch {
      return res.status(400).json({ error: "bad_request", detail: "JSON 형식이 아닙니다." });
    }
  }

  // 입력값의 자료형과 후보 수를 확인한다
  const problem = validateInput(body);
  if (problem) return res.status(400).json({ error: "bad_request", detail: problem });

  // 환경변수에서 키를 읽는다 (값은 절대 출력하지 않는다)
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    console.error("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.");
    return res.status(503).json({ error: "unavailable" });
  }

  // AI에게 넘길 조건과 후보 표
  const userInput = {
    condition: {
      season: body.season === "" ? "전체" : body.season,
      min_wins: body.minWins === null ? "없음" : body.minWins,
    },
    candidates: body.candidates.map((c) => ({ name: c.name, year: c.year, wins: c.wins, goals_for: c.goals_for })),
  };

  // 응답이 너무 늦으면 요청을 끊는다
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let geminiRes;
  try {
    geminiRes = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-goog-api-key": apiKey },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
        contents: [{ role: "user", parts: [{ text: "아래 조건과 후보 표에서 하나를 골라줘.\n" + JSON.stringify(userInput, null, 2) }] }],
        generationConfig: {
          responseMimeType: "application/json",
          responseSchema: RESPONSE_SCHEMA,
          temperature: 0.2,
        },
      }),
      signal: controller.signal,
    });
  } catch (err) {
    // 시간 초과나 네트워크 오류 (키가 담길 수 있는 요청 정보는 남기지 않는다)
    console.error("Gemini 호출 실패:", err.name);
    return res.status(503).json({ error: "unavailable" });
  } finally {
    clearTimeout(timer);
  }

  // 요청 한도 초과(429)나 그 밖의 오류 상태
  if (!geminiRes.ok) {
    console.error("Gemini 응답 상태:", geminiRes.status);
    return res.status(503).json({ error: "unavailable" });
  }

  // 응답에서 생성된 글자를 꺼낸다 (candidates[].content.parts[].text)
  let text = "";
  try {
    const data = await geminiRes.json();
    const parts = data?.candidates?.[0]?.content?.parts || [];
    text = parts.map((p) => (typeof p.text === "string" ? p.text : "")).join("");
  } catch {
    return res.status(503).json({ error: "unavailable" });
  }
  if (!text) return res.status(503).json({ error: "unavailable" });

  // JSON으로 읽고 후보·숫자를 검사한다
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    return res.status(422).json({ error: "unverified" });
  }
  const verified = verifyOutput(parsed, body.candidates);
  if (!verified) return res.status(422).json({ error: "unverified" });

  // 검사를 통과한 추천만 돌려준다
  return res.status(200).json(verified);
};
