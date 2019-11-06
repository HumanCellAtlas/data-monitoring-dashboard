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
    function getProjectBrowserUrl(projectUUID){
        urlBase = location.host.split('.').slice(1).join('.')
        return location.protocol + '//' + urlBase + '/explore/projects/' + projectUUID
    }
    function getSubmissionUIUrl(submissionUuid){
        urlBase = location.host.split('.').slice(1).join('.')
        return location.protocol + '//ui.ingest.' + urlBase + '/submissions/detail?uuid=' + submissionUuid
    }
    var dataSet = []
    projectsApiEndpoint = getTrackerApiUrl() + 'v0/projects'
    $.getJSON(projectsApiEndpoint, function(data) {
      $.each( data, function(key, val) {
        var projectUUID = val['project_uuid']
        var projectUUIDDisplay = "<a target='_blank' href='" + getProjectBrowserUrl(projectUUID) + "'>" + projectUUID + "</a>"

        projectInfo = val['project-info'][0]
        overallProjectState = projectInfo['project_state']
        overallProjectStateDisplay = convertTextToDisplayDiv(overallProjectState, overallProjectState)

        var ingestRecords = val['ingest-info']
        var submissionUuids = ''
        var ingestInfo = ingestRecords[0]
        $.each(ingestRecords, function(key, val){
            var submissionId = val['submission_id']
            var submissionUuid = val['submission_uuid']
            var submissionUuidDisplay = "<a target='_blank' href='" + getSubmissionUIUrl(submissionUuid) + "'>" + submissionUuid + "</a>"
            if(submissionId == projectInfo['latest_submission_id']){
                submissionUuids = submissionUuids + '<b>' + submissionUuidDisplay + '</b><br>'
                ingestInfo = val
            }
            else {
                submissionUuids = submissionUuids + submissionUuidDisplay + '<br>'
            }
        })
        var ingestPrimaryState = ingestInfo['primary_state']
        var ingestAnalysisState = 'COMPLETE'

        var azulInfo = val['azul-info'][0]
        var azulPrimaryState = azulInfo['primary_state']
        var azulAnalysisState = azulInfo['analysis_state']

        var dssInfo = val['dss-info'][0]
        var dssPrimaryState = dssInfo['primary_state']
        var dssAnalysisState = dssInfo['analysis_state']

        var matrixInfo = val['matrix-info'][0]
        var matrixAnalysisState = matrixInfo['analysis_state']

        var analysisInfo = val['analysis-info'][0]
        var analysisAnalysisState = analysisInfo['analysis_state']

        // PROJECT INFO DISPLAY
        var lastUpdatedAt = new Date(azulInfo['updated_at']).toLocaleString()
        var submissionDate = new Date(ingestInfo['submission_date']).toISOString().substring(0, 10);
        var githubIssueLink = "<a href='https://github.com/HumanCellAtlas/dcp/issues/" + projectInfo['github_issue'] + "'>Github Issue</a>"
        var projectLinkButton = "<button data-id='" + projectUUID + "' class='copy-button'>Shareable link</button>"
        var primaryInvestigatorDisplay = '<br><b>PIs: </b>' + ingestInfo['primary_investigator']
        var dataWranglerDisplay = '<b>Wranglers: </b>' + ingestInfo['data_curator']
        var projectTitle = '<b>' + ingestInfo['project_title'] + '</b><br>' + smallText(projectLinkButton) + '<br>' + smallText(primaryInvestigatorDisplay) + '<br>' + smallText(dataWranglerDisplay) + '<br><br>' + githubIssueLink
        var projectShortName = '<b>' + ingestInfo['project_short_name'] + '</b><br><smallText>Stats refreshed at: ' + lastUpdatedAt + '</smallText>'
        var submissionId = ingestInfo['submission_id']
        var species = azulInfo['species']
        var methods = azulInfo['library_construction_methods']

        // PRIMARY INFO DISPLAY
        var submissionStatus = ingestInfo['submission_status']
        var submissionStatusDisplay = convertTextToDisplayDiv(submissionStatus, ingestPrimaryState)

        var ingestPrimaryBundleCount = ingestInfo['submission_bundles_exported_count']
        ingestPrimaryBundleCountDisplay = convertTextToDisplayDiv(ingestPrimaryBundleCount, ingestPrimaryState)

        var dssAwsPrimaryBundleCount = dssInfo['aws_primary_bundle_count']
        var dssAwsAnalysisBundleCount = dssInfo['aws_analysis_bundle_count']
        var dssGcpPrimaryBundleCount = dssInfo['gcp_primary_bundle_count']
        var dssGcpAnalysisBundleCount = dssInfo['gcp_analysis_bundle_count']
        var dssAwsPrimaryBundleFQIDCount = dssInfo['aws_primary_bundle_fqids_count']
        var dssAwsAnalysisBundleFQIDCount = dssInfo['aws_analysis_bundle_fqids_count']
        var dssGcpPrimaryBundleFQIDCount = dssInfo['gcp_primary_bundle_fqids_count']
        var dssGcpAnalysisBundleFQIDCount = dssInfo['gcp_analysis_bundle_fqids_count']
        var dssPrimaryBundleCountDisplay = "<b>UUIDs</b><br> AWS: " + dssAwsPrimaryBundleCount + "<br>GCP: " + dssGcpPrimaryBundleCount +
            "<br><b>FQIDs</b><br> AWS: " + dssAwsPrimaryBundleFQIDCount + "<br>GCP: " + dssGcpPrimaryBundleFQIDCount
        var dssAnalysisBundleCountDisplay = "<b>UUIDs</b><br> AWS: " + dssAwsAnalysisBundleCount + "<br>GCP: " + dssGcpAnalysisBundleCount +
            "<br><b>FQIDs</b><br> AWS: " + dssAwsAnalysisBundleFQIDCount + "<br>GCP: " + dssGcpAnalysisBundleFQIDCount
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
            else if(key.includes('_v') ){
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

        var matrixAnalysisBundleCount = matrixInfo['analysis_bundle_count']
        var matrixCellCount = matrixInfo['cell_count']
        var projectMatricesCount = matrixInfo['project_matrices']
        matrixAnalysisBundleCountDisplay = convertTextToDisplayDiv(matrixAnalysisBundleCount, matrixAnalysisState)
        matrixCellCountDisplay = convertTextToDisplayDiv(matrixCellCount, matrixAnalysisState)
        projectMatricesCountDisplay = convertTextToDisplayDiv(projectMatricesCount, matrixAnalysisState)

        var project = [
            projectTitle,
            overallProjectStateDisplay,
            smallText(submissionDate),
            smallText(projectUUIDDisplay),
            smallText(submissionUuids),
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
            projectMatricesCountDisplay,
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
        order: [[ 2, "desc" ]],
        columnDefs: [
            {
               targets: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
               className: 'dt-left'
            },
            { type: 'num-html', targets: [8, 10, 14, 15, 16, 17, 18] }
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
