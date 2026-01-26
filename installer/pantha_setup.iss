#define MyAppName "Pantha Terminal"
#define MyAppExeName "PanthaTerminal.exe"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "V1LE-FARM"
#define MyAppURL "https://github.com/V1LE-FARM/pantha-terminal"

[Setup]
AppId={{A7C9A8B4-0F2A-4C5D-9E2A-1A1F9B8D9C01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=..\installer_output
OutputBaseFilename=PanthaSetup
Compression=lzma
SolidCompression=yes

SetupIconFile=..\assets\icon.ico
WizardStyle=modern

UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
