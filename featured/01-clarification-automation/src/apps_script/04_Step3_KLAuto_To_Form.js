function step3_klAutoToFormResponse() {
  const sourceSheet = openSheet_(
    PIPELINE_CFG.TASKMANAGER_SPREADSHEET_ID,
    PIPELINE_CFG.KL_AUTO_SHEET_NAME
  );

  const destSheet = openSheet_(
    PIPELINE_CFG.TASKMANAGER_SPREADSHEET_ID,
    PIPELINE_CFG.FORM_RESPONSE_SHEET_NAME
  );

  const sourceLastRow = sourceSheet.getLastRow();

  if (sourceLastRow < 2) {
    return {
      step: "Step 3",
      sourceRows: 0,
      groupedKeys: 0,
      updatedRows: 0,
      missingDestinationRows: 0,
      duplicateDestinationKeys: 0
    };
  }

  const sourceValues = sourceSheet
    .getRange(2, 1, sourceLastRow - 1, 16)
    .getValues()
    .filter(row => isDateInRunWindow_(row[2]))
    .filter(row => normalizeEmail_(row[15]) !== "");

  /**
   * Group source rows before writing to destination.
   *
   * KL_Auto can contain multiple rows for the same employee/date because:
   * - employee worked in shift 1 and shift 2
   * - employee worked across different workplaces
   * - manual + auto data both contribute to the same final form row
   *
   * Final destination 01.10.2021 is matched by:
   * date + email + Tätigkeitsbereich
   *
   * Therefore source must be grouped by:
   * date + email
   *
   * Name is stored for audit only, not used as the final matching key.
   */
  const grouped = new Map();

  sourceValues.forEach(row => {
    const dateKey = toDateKey_(row[2]);          // C Datum
    const name = normalizeText_(row[4]);         // E Mitarbeiter
    const email = normalizeEmail_(row[15]);      // P Email

    if (!dateKey || !email) return;

    const lookupKey = buildKlaerfallLookupKey_(dateKey, email);

    if (!grouped.has(lookupKey)) {
      grouped.set(lookupKey, {
        dateKey,
        email,
        names: new Set(),

        total: 0,
        warengruppe: 0,
        uebermenge: 0,
        ohneMaengel: 0,
        ohnePreis: 0,
        qualitaet: 0,
        sonstiges: 0
      });
    }

    const item = grouped.get(lookupKey);

    if (name) {
      item.names.add(name);
    }

    item.warengruppe += toNumber_(row[6]);   // G Falsche Warengruppe
    item.uebermenge += toNumber_(row[7]);    // H Übermenge
    item.ohnePreis += toNumber_(row[8]);     // I Ohne Preis
    item.sonstiges += toNumber_(row[9]);     // J Sonstiges
    item.ohneMaengel += toNumber_(row[10]);  // K Ohne Mängel
    item.qualitaet += toNumber_(row[11]);    // L Qualitätsproblem
    item.total += toNumber_(row[12]);        // M Gesamtanzahl
  });

  const destLastRow = destSheet.getLastRow();

  if (destLastRow < 2) {
    throw new Error(
      "Destination form-response sheet has no data rows: " +
      PIPELINE_CFG.FORM_RESPONSE_SHEET_NAME
    );
  }

  const destValues = destSheet
    .getRange(2, 1, destLastRow - 1, 20)
    .getValues();

  const destKeyToRows = new Map();

  destValues.forEach((row, index) => {
    const timestamp = row[0];                 // A Zeitstempel
    const email = normalizeEmail_(row[1]);    // B E-Mail-Adresse
    const taskArea = normalizeText_(row[2]);  // C Tätigkeitsbereich

    if (!timestamp || !email || taskArea !== PIPELINE_CFG.TASK_AREA) return;
    if (!isDateInRunWindow_(timestamp)) return;

    const dateKey = toDateKey_(timestamp);
    const lookupKey = buildKlaerfallLookupKey_(dateKey, email);
    const sheetRowNumber = index + 2;

    if (!destKeyToRows.has(lookupKey)) {
      destKeyToRows.set(lookupKey, []);
    }

    destKeyToRows.get(lookupKey).push(sheetRowNumber);
  });

  let updatedRows = 0;
  const missingDestinationRows = [];
  const duplicateDestinationKeys = [];

  grouped.forEach((item, lookupKey) => {
    const updateValues = [
      item.total,        // N Klärfall - Gesamtanzahl
      item.warengruppe,  // O Klärfall - Warengruppe
      item.uebermenge,   // P Klärfall - Übermenge
      item.ohneMaengel,  // Q Klärfall - Ohne Mängel
      item.ohnePreis,    // R Klärfall - Ohne Preis
      item.qualitaet,    // S Klärfall - Qualität
      item.sonstiges     // T Klärfall - Sonstiges
    ];

    if (!destKeyToRows.has(lookupKey)) {
      missingDestinationRows.push({
        key: lookupKey,
        date: item.dateKey,
        email: item.email,
        names: Array.from(item.names).join(", ")
      });
      return;
    }

    const matchingRows = destKeyToRows.get(lookupKey);

    if (matchingRows.length > 1) {
      duplicateDestinationKeys.push({
        key: lookupKey,
        rows: matchingRows.join(", "),
        names: Array.from(item.names).join(", ")
      });
    }

    const targetRow = matchingRows[matchingRows.length - 1];

    destSheet
      .getRange(targetRow, 14, 1, 7)
      .setValues([updateValues]);

    updatedRows++;
  });

  return {
    step: "Step 3: KL_Auto -> 01.10.2021",
    sourceRows: sourceValues.length,
    groupedKeys: grouped.size,
    updatedRows,
    missingDestinationRows: missingDestinationRows.length,
    duplicateDestinationKeys: duplicateDestinationKeys.length,
    missingExamples: missingDestinationRows.slice(0, 10),
    duplicateExamples: duplicateDestinationKeys.slice(0, 10)
  };
}