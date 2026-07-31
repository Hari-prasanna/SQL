function createDailyKlaerfallPipelineTrigger() {
  const triggers = ScriptApp.getProjectTriggers();

  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === "runFullKlPipelineScheduled") {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger("runFullKlPipelineScheduled")
    .timeBased()
    .everyDays(1)
    .atHour(3)
    .create();
}

function runFullKlPipelineScheduled() {
  runFullKlPipeline_("scheduled_03_00");
}