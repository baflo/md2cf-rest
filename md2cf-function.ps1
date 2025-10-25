<#
.SYNOPSIS
PowerShell wrapper function for md2cf Docker container

.DESCRIPTION
This script provides a PowerShell function to easily use md2cf via Docker.
It can be dot-sourced into your PowerShell session or added to your PowerShell profile.

.NOTES
Author: md2cf team
Version: 1.0.0
Requires: Docker Desktop for Windows

.EXAMPLE
# Load the function
. .\md2cf-function.ps1

# Use it
md2cf publish README.md --space DEMO --title "My Document"
#>

function md2cf {
    <#
    .SYNOPSIS
    Convert Markdown to Confluence Storage Format and publish to Confluence

    .DESCRIPTION
    Wrapper function for md2cf Docker container that converts Markdown files to Confluence format
    and can publish them directly to Confluence.

    .PARAMETER Arguments
    Additional arguments to pass to md2cf

    .EXAMPLE
    md2cf convert README.md

    .EXAMPLE
    md2cf convert README.md -o output.html

    .EXAMPLE
    md2cf publish README.md --space DEMO --title "My Document"

    .EXAMPLE
    md2cf publish docs/api.md --space DEMO --title "API Documentation" --parent-id 123456

    .EXAMPLE
    md2cf download-attachment 813134619 document.md -o ./document.md

    .NOTES
    Requires Docker to be installed and running.
    Uses environment variables CONFLUENCE_URL, JIRA_URL and CONFLUENCE_TOKEN if set.
    #>

    [CmdletBinding()]
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Arguments
    )

    # Docker Befehl zusammenbauen mit relativem Pfad
    $dockerArgs = @(
        'run'
        '--rm'
        '-v'
        './:/workspace'
        '--workdir=/workspace'
    )

    # Umgebungsvariablen hinzufügen, falls gesetzt
    if ($env:CONFLUENCE_URL) {
        $dockerArgs += '-e'
        $dockerArgs += "CONFLUENCE_URL=$env:CONFLUENCE_URL"
    }

    if ($env:JIRA_URL) {
        $dockerArgs += '-e'
        $dockerArgs += "JIRA_URL=$env:JIRA_URL"
    }

    if ($env:CONFLUENCE_TOKEN) {
        $dockerArgs += '-e'
        $dockerArgs += "CONFLUENCE_TOKEN=$env:CONFLUENCE_TOKEN"
    }

    if ($env:CONFLUENCE_SPACE) {
        $dockerArgs += '-e'
        $dockerArgs += "CONFLUENCE_SPACE=$env:CONFLUENCE_SPACE"
    }

    # Image und Befehl hinzufügen
    $dockerArgs += 'md2cf'
    $dockerArgs += 'md2cf'

    # Benutzer-Argumente hinzufügen
    if ($Arguments) {
        $dockerArgs += $Arguments
    }

    # Docker Befehl ausführen
    & docker $dockerArgs
}

# Export the function
Export-ModuleMember -Function md2cf
