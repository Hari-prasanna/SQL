const PIPELINE_CFG = {
  TIMEZONE: "Europe/Berlin",

  // Optional hard minimum date.
  // Keep empty for automatic rolling lookback.
  // Example: "2026-07-13" means never process rows before 13.07.2026.
  PIPELINE_MIN_DATE_KEY: "2026-07-13",

  // Current day + previous 5 calendar days.
  LOOKBACK_DAYS_BACK: 5,

  /***********************
   * SPREADSHEET IDS
   ***********************/

  // Manual clarification-case support sheet
  MANUAL_SOURCE_SPREADSHEET_ID: "",

  // Combined auto + manual staging sheet
  AUTO_MANUAL_SPREADSHEET_ID: "",

  // Final team reporting workbook ("Taskmanager")
  TASKMANAGER_SPREADSHEET_ID: "",

  /***********************
   * SHEET NAMES
   ***********************/

  MANUAL_SUPPORT_SHEET_NAME: "Manual - Support",
  MANUAL_RAW_SHEET_NAME: "manual_raw",

  AUTO_RAW_SHEET_NAME: "auto_raw",
  AUTO_MANUAL_SHEET_NAME: "auto+manual",

  KL_AUTO_SHEET_NAME: "KL_Auto",
  FORM_RESPONSE_SHEET_NAME: "01.10.2021",

  TASK_AREA: "Klärfallbearbeitung"
};