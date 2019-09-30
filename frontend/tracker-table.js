String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1)
}

function smallText(str){
    return `<smallText>${str}</smallText>`
}

function coloredDiv(str, color) {
    return `<div class="${color}">${str}</div>`
}

function convertTextToDisplayDiv(text, status){
    if(status == 'INCOMPLETE'){
        return coloredDiv(smallText(text), "red")
    }
    else if(status == 'OUT_OF_DATE'){
        return coloredDiv(smallText(text), "yellow")
    }
    else{
        return smallText(text)
    }
}

$(document).ready(function() {
    var currentUrl = location.protocol + '//' + location.host + location.pathname
    function getTrackerApiUrl() {
        apiUrl = currentUrl.replace('tracker', 'tracker-api')
        if (location.host.endsWith(":8000")) {
            apiUrl = currentUrl.replace(":8000", ":9000")
        }
        return apiUrl
    }

    function getProjectTrackerUrl(projectUUID){
        projectTrackerUrl = currentUrl + '?projectUUID=' + projectUUID
        return projectTrackerUrl
    }
    var dataSet = []
    projectsApiEndpoint = getTrackerApiUrl() + 'v0/projects'
    $.getJSON(projectsApiEndpoint, function(data) {
      $.each( data, function(key, val) {
        var projectUUID = val['project_uuid']

        ingestInfo = val['ingest-info']
        ingestPrimaryState = ingestInfo['primary_state']
        ingestAnalysisState = 'COMPLETE'

        azulInfo = val['azul-info']
        azulPrimaryState = azulInfo['primary_state']
        azulAnalysisState = azulInfo['analysis_state']

        dssInfo = val['dss-info']
        dssPrimaryState = dssInfo['primary_state']
        dssAnalysisState = dssInfo['analysis_state']

        matrixInfo = val['matrix-info']
        matrixAnalysisState = matrixInfo['analysis_state']

        analysisInfo = val['analysis-info']
        analysisAnalysisState = analysisInfo['analysis_state']

        // PROJECT INFO DISPLAY
        var lastUpdatedAt = new Date(azulInfo['updated_at']).toLocaleString()
        var submissionDate = new Date(ingestInfo['submission_date']).toISOString().substring(0, 10);
        var projectLinkButton = "<button data-id='" + projectUUID + "' class='copy-button'>Shareable link</button>"
        var primaryInvestigatorDisplay = '<br><b>PIs: </b>' + ingestInfo['primary_investigator']
        var dataWranglerDisplay = '<b>Wranglers: </b>' + ingestInfo['data_curator']
        var projectTitle = '<b>' + ingestInfo['project_title'] + '</b><br>' + smallText(projectLinkButton) + '<br>' + smallText(primaryInvestigatorDisplay) + '<br>' + smallText(dataWranglerDisplay)
        var projectShortName = '<b>' + ingestInfo['project_short_name'] + '</b><br><smallText>Stats refreshed at: ' + lastUpdatedAt + '</smallText>'
        var submissionId = ingestInfo['submission_id']
        var species = azulInfo['species']
        var methods = azulInfo['library_construction_methods']

        // PRIMARY INFO DISPLAY
        var submissionStatus = ingestInfo['submission_status']
        var submissionStatusDisplay = convertTextToDisplayDiv(submissionStatus, ingestPrimaryState)

        var ingestPrimaryBundleCount = ingestInfo['submission_bundles_exported_count']
        // This submission has the incorrect bundle count but has been resolved. Manually overriding.
        if(submissionId == '5cda8757d96dad000856d2ae'){
            ingestPrimaryBundleCount = '3514'
        }
        ingestPrimaryBundleCountDisplay = convertTextToDisplayDiv(ingestPrimaryBundleCount, ingestPrimaryState)

        var dssAwsPrimaryBundleCount = dssInfo['aws_primary_bundle_count']
        var dssAwsAnalysisBundleCount = dssInfo['aws_analysis_bundle_count']
        var dssGcpPrimaryBundleCount = dssInfo['gcp_primary_bundle_count']
        var dssGcpAnalysisBundleCount = dssInfo['gcp_analysis_bundle_count']
        var dssPrimaryBundleCountDisplay = "AWS: " + dssAwsPrimaryBundleCount + "<br>GCP: " + dssGcpPrimaryBundleCount
        var dssAnalysisBundleCountDisplay = "AWS: " + dssAwsAnalysisBundleCount + "<br>GCP: " + dssGcpAnalysisBundleCount
        dssPrimaryBundleCountDisplay = convertTextToDisplayDiv(dssPrimaryBundleCountDisplay, dssPrimaryState)
        dssAnalysisBundleCountDisplay = convertTextToDisplayDiv(dssAnalysisBundleCountDisplay, dssAnalysisState)

        // ANALYSIS INFO DISPLAY
        var project_workflows_job_manager_link_template = 'https://job-manager.caas-prod.broadinstitute.org/jobs?q=project_uuid%3D{PROJECT_UUID}'
        var project_and_status_job_manager_link_template = 'https://job-manager.caas-prod.broadinstitute.org/jobs?q=project_uuid%3D{PROJECT_UUID}%26status%3D{WORKFLOW_STATUS}'
        var project_and_version_job_manager_link_template = 'https://job-manager.caas-prod.broadinstitute.org/jobs?q=project_uuid%3D{PROJECT_UUID}%26workflow-version%3D{WORKFLOW_VERSION}'
        var workflowLink = project_workflows_job_manager_link_template.replace('{PROJECT_UUID}', projectUUID)
        var workflowStatsByStatusDisplay = '<a href="' + workflowLink + '"target="_blank">' + 'Total: ' + analysisInfo['total_workflows'] + '</a>' + '<br>'
        var workflowStatsByVersionDisplay = '<a href="' + workflowLink + '"target="_blank">' + 'Total: ' + analysisInfo['total_workflows'] + '</a>' + '<br>'
        $.each(analysisInfo, function(key, val) {
            if(key.includes('_workflows') && key != 'total_workflows'){
                var workflowStatus = key.split('_workflows')[0].capitalize()
                var workflowLink = project_and_status_job_manager_link_template.replace('{PROJECT_UUID}', projectUUID).replace('{WORKFLOW_STATUS}', workflowStatus)
                var worfklowStatusMessage = '<a href="' + workflowLink + '"target="_blank">' + workflowStatus + ': ' + val + '</a>'
                workflowStatsByStatusDisplay = workflowStatsByStatusDisplay + worfklowStatusMessage + '<br>'
            }
            else if(key != 'total_workflows' && key != 'analysis_state' && key != 'updated_at' && key != 'project_uuid'){
                var workflowLink = project_and_version_job_manager_link_template.replace('{PROJECT_UUID}', projectUUID).replace('{WORKFLOW_VERSION}', key)
                var worfklowVersionMessage = '<a href="' + workflowLink + '"target="_blank">' + key + ': ' + val + '</a>'
                workflowStatsByVersionDisplay = workflowStatsByVersionDisplay + worfklowVersionMessage + '<br>'
            }
        })
        workflowStatsByStatusDisplay = convertTextToDisplayDiv(workflowStatsByStatusDisplay, analysisAnalysisState)
        workflowStatsByVersionDisplay = convertTextToDisplayDiv(workflowStatsByVersionDisplay, analysisAnalysisState)

        analysisEnvelopesDisplay = 'Total' + ': ' + ingestInfo['Total_envelopes'] + '<br>'
        $.each(ingestInfo, function(key, val) {
            if(key.includes('_envelopes') && key != 'Total_envelopes'){
                var envelopeStatus = key.split('_envelopes')[0].capitalize()
                analysisEnvelopesDisplay = analysisEnvelopesDisplay + envelopeStatus + ': ' + val + '<br>'
            }
        })
        analysisEnvelopesDisplay = convertTextToDisplayDiv(analysisEnvelopesDisplay, ingestAnalysisState)

        var azulPrimaryBundleCount = azulInfo['primary_bundle_count']
        var azulAnalysisBundleCount = azulInfo['analysis_bundle_count']
        azulPrimaryBundleCountDisplay = convertTextToDisplayDiv(azulPrimaryBundleCount, azulPrimaryState)
        azulAnalysisBundleCountDisplay = convertTextToDisplayDiv(azulAnalysisBundleCount, azulAnalysisState)

        matrixInfo = val['matrix-info']
        var matrixAnalysisBundleCount = matrixInfo['analysis_bundle_count']
        var matrixCellCount = matrixInfo['cell_count']
        matrixAnalysisBundleCountDisplay = convertTextToDisplayDiv(matrixAnalysisBundleCount, matrixAnalysisState)
        matrixCellCountDisplay = convertTextToDisplayDiv(matrixCellCount, matrixAnalysisState)

        var project = [
            projectTitle,
            smallText(submissionDate),
            smallText(projectUUID),
            smallText(submissionId),
            smallText(species),
            smallText(methods),
            submissionStatusDisplay,
            ingestPrimaryBundleCountDisplay,
            dssPrimaryBundleCountDisplay,
            azulPrimaryBundleCountDisplay,
            workflowStatsByStatusDisplay,
            workflowStatsByVersionDisplay,
            analysisEnvelopesDisplay,
            dssAnalysisBundleCountDisplay,
            azulAnalysisBundleCountDisplay,
            matrixAnalysisBundleCountDisplay,
            matrixCellCountDisplay,
            projectShortName
        ]

        if(parseInt(dssAwsPrimaryBundleCount) > 0 || parseInt(dssAwsAnalysisBundleCount) > 0 || parseInt(dssGcpPrimaryBundleCount) > 0 || parseInt(dssGcpAnalysisBundleCount) > 0 || parseInt(azulPrimaryBundleCount) > 0 || parseInt(azulAnalysisBundleCount) > 0 || parseInt(matrixAnalysisBundleCount) > 0) {
            dataSet.push(project);
        }
      });
      jQuery.extend( jQuery.fn.dataTableExt.oSort, {
        "num-html-pre": function ( a ) {
            var x = String(a).replace( /<[\s\S]*?>/g, "" );
            return parseFloat( x );
        },
        "num-html-asc": function ( a, b ) {
            return ((a < b) ? -1 : ((a > b) ? 1 : 0));
        },
        "num-html-desc": function ( a, b ) {
            return ((a < b) ? 1 : ((a > b) ? -1 : 0));
        }
      });
      function getUrlVars() {
        var vars = {};
        var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
          vars[key] = value;
        });
        return vars;
      }
      function getUrlParam(parameter, defaultvalue){
        var urlparameter = defaultvalue;
        if(window.location.href.indexOf(parameter) > -1){
          urlparameter = getUrlVars()[parameter];
        }
        return urlparameter;
      }
      $('#tracker').DataTable({
        oSearch: {"sSearch": getUrlParam('projectUUID', '')},
        paging: false,
        data: dataSet,
        order: [[ 1, "desc" ]],
        columnDefs: [
            {
               targets: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
               className: 'dt-left'
            },
            { type: 'num-html', targets: [7, 9, 13, 14, 15] }
        ],
        drawCallback: function( settings ) {
            $('.red').parent('.dt-left').css('background', '#f5dad6');
            $('.red').parent('.dt-left').prop('title', 'Data is incomplete. Further investigation required');
            $('.yellow').parent('.dt-left').css('background', '#ffae00');
            $('.yellow').parent('.dt-left').prop('title', 'Data is not up to date. Further investigation required');
            $('.copy-button').on('click', function () {
                var projectUUID = $(this).data('id')
                projectTrackerUrl = getProjectTrackerUrl(projectUUID)
                alert("Copy this url: " + projectTrackerUrl);
            });
        }
      });
      $('#tracker_filter').css("color", "#b92525");
      $('#tracker_filter').css("font-size", "25px");
      $('#tracker_filter').css("float", "left");
      $('#tracker_length').css("float", "right");
      $('input').css("width", "300px");
      $('.lds-ring').hide();
      $('#tracker').show();
      $('#github_link').show();
    });
})
