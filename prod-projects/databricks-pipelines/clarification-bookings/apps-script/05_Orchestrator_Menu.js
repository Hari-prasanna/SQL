function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("Klärfall Pipeline")
    .addItem("Run full sequence", "runFullKlPipelineFromMenu")
    .addItem("Run only Step 3", "runOnlyStep3FromMenu")
    .addToUi();
}

function runFullKlPipelineFromMenu() {
  try {
    const result = runFullKlPipeline_("manual_menu");

    const step1 = result.results[0].result;
    const step2 = result.results[1].result;
    const step3 = result.results[2].result;

    const message =
      "Klärfall pipeline completed successfully.\n\n" +
      "Date window: " + result.window.startKey + " to " + result.window.endKey + "\n\n" +
      "Step 1 - Manual Support to manual_raw\n" +
      "Updated: " + step1.updatedRows + "\n" +
      "Added: " + step1.appendedRows + "\n\n" +
      "Step 2 - auto+manual to KL_Auto\n" +
      "Updated: " + step2.updatedRows + "\n" +
      "Added: " + step2.appendedRows + "\n\n" +
      "Step 3 - KL_Auto to 01.10.2021\n" +
      "Updated: " + step3.updatedRows + "\n" +
      "Missing form rows: " + step3.missingDestinationRows + "\n" +
      "Duplicate form keys: " + step3.duplicateDestinationKeys;

    SpreadsheetApp.getUi().alert(message);

  } catch (err) {
    sendPipelineFailureCard_("Klärfall pipeline failed", err, "manual_menu");

    SpreadsheetApp.getUi().alert(
      "Pipeline failed.\n\n" +
      "Failed step: " + (err.stepName || "Unknown") + "\n" +
      "Error: " + err.message + "\n\n" +
      "Check Apps Script executions or the Google Chat alert."
    );

    throw err;
  }
}

function runOnlyStep3FromMenu() {
  try {
    const result = step3_klAutoToFormResponse();

    SpreadsheetApp.getUi().alert(
      "Step 3 complete.\n\n" + JSON.stringify(result, null, 2)
    );

  } catch (err) {
    sendPipelineFailureCard_("Step 3 failed", err, "manual_menu_step3_only");

    SpreadsheetApp.getUi().alert(
      "Step 3 failed:\n\n" +
      err.message +
      "\n\nCheck Apps Script executions and the Google Chat alert."
    );

    throw err;
  }
}

function runFullKlPipeline_(triggeredBy) {
  const lock = LockService.getScriptLock();

  try {
    lock.waitLock(30000);

    const startedAt = new Date();
    const window = getRunDateWindow_();

    const results = [];

    results.push(runPipelineStep_("Step 1: Manual - Support -> manual_raw", step1_manualSupportToManualRaw));
    SpreadsheetApp.flush();

    results.push(runPipelineStep_("Step 2: auto+manual -> KL_Auto", step2_autoManualToKlAuto));
    SpreadsheetApp.flush();

    results.push(runPipelineStep_("Step 3: KL_Auto -> 01.10.2021", step3_klAutoToFormResponse));
    SpreadsheetApp.flush();

    const output = {
      status: "SUCCESS",
      triggeredBy,
      window,
      startedAt,
      finishedAt: new Date(),
      results
    };

    Logger.log(JSON.stringify(output, null, 2));

    return output;

  } catch (err) {
    sendPipelineFailureCard_("Klärfall pipeline failed", err, triggeredBy);
    throw err;

  } finally {
    try {
      lock.releaseLock();
    } catch (ignore) {}
  }
}

function runPipelineStep_(stepName, fn) {
  const startedAt = new Date();

  try {
    const result = fn();

    return {
      step: stepName,
      status: "SUCCESS",
      startedAt,
      finishedAt: new Date(),
      result
    };

  } catch (err) {
    err.stepName = stepName;
    throw err;
  }
}

function doPost(e) {
  try {
    const body = e && e.postData && e.postData.contents
      ? JSON.parse(e.postData.contents)
      : {};

    const expectedToken = PropertiesService
      .getScriptProperties()
      .getProperty(PIPELINE_CFG.PIPELINE_TOKEN_PROPERTY);

    if (!expectedToken) {
      throw new Error("Missing Script Property: " + PIPELINE_CFG.PIPELINE_TOKEN_PROPERTY);
    }

    if (body.token !== expectedToken) {
      throw new Error("Unauthorized pipeline trigger. Invalid token.");
    }

    const result = runFullKlPipeline_("databricks_webhook");

    return ContentService
      .createTextOutput(JSON.stringify({
        status: "OK",
        result
      }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    sendPipelineFailureCard_("Databricks-triggered pipeline failed", err, "databricks_webhook");

    return ContentService
      .createTextOutput(JSON.stringify({
        status: "ERROR",
        message: err.message
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}