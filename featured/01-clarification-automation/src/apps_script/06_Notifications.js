function sendPipelineFailureCard_(title, err, triggeredBy) {
  const webhookUrl = PropertiesService
    .getScriptProperties()
    .getProperty(PIPELINE_CFG.CHAT_WEBHOOK_URL_PROPERTY);

  if (!webhookUrl) {
    Logger.log("CHAT_WEBHOOK_URL not configured. Error: " + err.message);
    return;
  }

  const stepName = err.stepName || "Unknown step";

  const payload = {
    cardsV2: [
      {
        cardId: "klarfall-pipeline-failure",
        card: {
          header: {
            title: "Klärfall pipeline failed",
            subtitle: "Triggered by: " + triggeredBy
          },
          sections: [
            {
              header: "What happened",
              widgets: [
                {
                  decoratedText: {
                    topLabel: "Failed step",
                    text: stepName
                  }
                },
                {
                  decoratedText: {
                    topLabel: "Error message",
                    text: String(err.message || err)
                  }
                }
              ]
            },
            {
              header: "What to do",
              widgets: [
                {
                  decoratedText: {
                    text:
                      "1. Open the Taskmanager reporting workbook.\n" +
                      "2. Use menu: Klärfall Pipeline > Run full sequence.\n" +
                      "3. If it fails again, check Apps Script Executions.\n" +
                      "4. Verify spreadsheet IDs, sheet names, date window, and column layout."
                  }
                }
              ]
            }
          ]
        }
      }
    ]
  };

  UrlFetchApp.fetch(webhookUrl, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
}