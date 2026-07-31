function openSheet_(spreadsheetId, sheetName) {
  const ss = SpreadsheetApp.openById(spreadsheetId);
  const sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    throw new Error("Sheet not found: " + sheetName + " in spreadsheet " + spreadsheetId);
  }

  return sheet;
}

function getRunDateWindow_() {
  const today = new Date();

  const windowStart = new Date(today);
  windowStart.setDate(today.getDate() - PIPELINE_CFG.LOOKBACK_DAYS_BACK);

  let startKey = Utilities.formatDate(
    windowStart,
    PIPELINE_CFG.TIMEZONE,
    "yyyy-MM-dd"
  );

  const endKey = Utilities.formatDate(
    today,
    PIPELINE_CFG.TIMEZONE,
    "yyyy-MM-dd"
  );

  // Optional hard floor.
  // If PIPELINE_MIN_DATE_KEY is empty, use normal rolling window.
  if (
    PIPELINE_CFG.PIPELINE_MIN_DATE_KEY &&
    startKey < PIPELINE_CFG.PIPELINE_MIN_DATE_KEY
  ) {
    startKey = PIPELINE_CFG.PIPELINE_MIN_DATE_KEY;
  }

  return {
    startKey,
    endKey
  };
}

function isDateInRunWindow_(value) {
  const dateKey = toDateKey_(value);
  if (!dateKey) return false;

  const window = getRunDateWindow_();

  return dateKey >= window.startKey && dateKey <= window.endKey;
}

function toDateKey_(value) {
  if (Object.prototype.toString.call(value) === "[object Date]" && !isNaN(value)) {
    return Utilities.formatDate(value, PIPELINE_CFG.TIMEZONE, "yyyy-MM-dd");
  }

  const s = String(value || "").trim();

  // Handles "01.07.2026" and "01.07.2026 14:41:17"
  const germanDateMatch = s.match(/^(\d{2})\.(\d{2})\.(\d{4})/);

  if (germanDateMatch) {
    const day = germanDateMatch[1];
    const month = germanDateMatch[2];
    const year = germanDateMatch[3];

    return year + "-" + month + "-" + day;
  }

  const parsed = new Date(s);

  if (!isNaN(parsed)) {
    return Utilities.formatDate(parsed, PIPELINE_CFG.TIMEZONE, "yyyy-MM-dd");
  }

  return "";
}

function normalizeText_(value) {
  return String(value || "").trim();
}

function normalizeEmail_(value) {
  return String(value || "").trim().toLowerCase();
}

function toNumber_(value) {
  if (value === "" || value === null || value === undefined) return 0;

  const n = Number(String(value).replace(",", "."));

  return isNaN(n) ? 0 : n;
}

function buildKeyToRowMap_(sheet, keyCol, startRow) {
  const lastRow = sheet.getLastRow();
  const map = new Map();

  if (lastRow < startRow) return map;

  const values = sheet
    .getRange(startRow, keyCol, lastRow - startRow + 1, 1)
    .getValues();

  values.forEach((row, index) => {
    const key = normalizeText_(row[0]);

    if (key) {
      map.set(key, index + startRow);
    }
  });

  return map;
}

function buildKlaerfallLookupKey_(dateKey, email) {
  return [
    dateKey,
    normalizeEmail_(email),
    PIPELINE_CFG.TASK_AREA
  ].join("|");
}