function step2_autoManualToKlAuto() {
  const sourceSheet = openSheet_(
    PIPELINE_CFG.AUTO_MANUAL_SPREADSHEET_ID,
    PIPELINE_CFG.AUTO_MANUAL_SHEET_NAME
  );

  const destSheet = openSheet_(
    PIPELINE_CFG.TASKMANAGER_SPREADSHEET_ID,
    PIPELINE_CFG.KL_AUTO_SHEET_NAME
  );

  const sourceLastRow = sourceSheet.getLastRow();

  if (sourceLastRow < 2) {
    return {
      step: "Step 2",
      sourceRows: 0,
      updatedRows: 0,
      appendedRows: 0
    };
  }

  // Source auto+manual:
  // A Unique_id
  // B Datum
  // C Schicht
  // D Mitarbeiter
  // E Arbeitsplatz
  // F Falsche Warengruppe
  // G Übermenge
  // H Ohne Preis
  // I Sonstiges
  // J Ohne Mängel
  // K Qualitätsproblem_auto
  // L Gesamtanzahl
  const sourceValues = sourceSheet
    .getRange(2, 1, sourceLastRow - 1, 12)
    .getValues()
    .filter(row => normalizeText_(row[0]) !== "")
    .filter(row => isDateInRunWindow_(row[1]));

  const keyToRow = buildKeyToRowMap_(destSheet, 2, 2); // KL_Auto column B = Unique_id

  const now = new Date();
  const rowsToAppend = [];
  let updatedRows = 0;

  sourceValues.forEach(row => {
    const uniqueId = normalizeText_(row[0]);

    const outputWithoutRecordId = [
      uniqueId,                  // B Unique_id
      row[1],                    // C Datum
      row[2],                    // D Schicht
      row[3],                    // E Mitarbeiter
      row[4],                    // F Arbeitsplatz
      row[5],                    // G Falsche Warengruppe
      row[6],                    // H Übermenge
      row[7],                    // I Ohne Preis
      row[8],                    // J Sonstiges
      row[9],                    // K Ohne Mängel
      row[10],                   // L Qualitätsproblem
      row[11],                   // M Gesamtanzahl
      PIPELINE_CFG.AUTO_MANUAL_SHEET_NAME, // N source_sheet
      now                        // O last_updated_at
    ];

    if (keyToRow.has(uniqueId)) {
      const targetRow = keyToRow.get(uniqueId);

      // Update B:O only.
      // Column A record_id stays unchanged.
      // Column P Email is not touched, because it may be formula-generated.
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

  SpreadsheetApp.flush();

  return {
    step: "Step 2: auto+manual -> KL_Auto",
    sourceRows: sourceValues.length,
    updatedRows,
    appendedRows: rowsToAppend.length
  };
}