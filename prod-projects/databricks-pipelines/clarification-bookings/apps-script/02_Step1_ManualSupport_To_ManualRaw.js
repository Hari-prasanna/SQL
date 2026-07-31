function step1_manualSupportToManualRaw() {
  const sourceSheet = openSheet_(
    PIPELINE_CFG.MANUAL_SOURCE_SPREADSHEET_ID,
    PIPELINE_CFG.MANUAL_SUPPORT_SHEET_NAME
  );

  const destSheet = openSheet_(
    PIPELINE_CFG.AUTO_MANUAL_SPREADSHEET_ID,
    PIPELINE_CFG.MANUAL_RAW_SHEET_NAME
  );

  const sourceLastRow = sourceSheet.getLastRow();

  if (sourceLastRow < 2) {
    return {
      step: "Step 1",
      sourceRows: 0,
      updatedRows: 0,
      appendedRows: 0
    };
  }

  // Source:
  // A Unique_key
  // B Datum
  // C SHIFT
  // D Mitarbeiter
  // E Arbeitsplatz
  // F Falsche Warengruppe
  // G Übermenge
  // H Ohne Preis
  // I Ohne Mängel
  // J Qualitätsproblem
  // K Sonstiges
  const sourceValues = sourceSheet
    .getRange(2, 1, sourceLastRow - 1, 11)
    .getValues()
    .filter(row => normalizeText_(row[0]) !== "")
    .filter(row => isDateInRunWindow_(row[1]));

  const keyToRow = buildKeyToRowMap_(destSheet, 2, 2); // destination column B = Unique_key

  const now = new Date();
  const rowsToAppend = [];
  let updatedRows = 0;

  sourceValues.forEach(row => {
    const uniqueKey = normalizeText_(row[0]);

    const outputWithoutRecordId = [
      uniqueKey,                 // B Unique_key
      row[1],                    // C Datum
      row[2],                    // D SHIFT
      row[3],                    // E Mitarbeiter
      row[4],                    // F Arbeitsplatz
      row[5],                    // G Falsche Warengruppe
      row[6],                    // H Übermenge
      row[7],                    // I Ohne Preis
      row[8],                    // J Ohne Mängel
      row[9],                    // K Qualitätsproblem
      row[10],                   // L Sonstiges
      PIPELINE_CFG.MANUAL_SUPPORT_SHEET_NAME, // M source_sheet
      now                        // N last_updated_at
    ];

    if (keyToRow.has(uniqueKey)) {
      const targetRow = keyToRow.get(uniqueKey);

      // Update B:N, keep A record_id
      destSheet
        .getRange(targetRow, 2, 1, outputWithoutRecordId.length)
        .setValues([outputWithoutRecordId]);

      updatedRows++;
    } else {
      rowsToAppend.push([
        Utilities.getUuid(),     // A record_id
        ...outputWithoutRecordId
      ]);
    }
  });

  if (rowsToAppend.length > 0) {
    destSheet
      .getRange(destSheet.getLastRow() + 1, 1, rowsToAppend.length, rowsToAppend[0].length)
      .setValues(rowsToAppend);
  }

  return {
    step: "Step 1: Manual - Support -> manual_raw",
    sourceRows: sourceValues.length,
    updatedRows,
    appendedRows: rowsToAppend.length
  };
}