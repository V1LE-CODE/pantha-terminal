#define MyAppName "Pantha Terminal"
#define MyAppExeName "PanthaTerminal.exe"
#define MyAppPublisher "Pantha"
#define MyAppURL "https://github.com/V1LE-FARM/pantha-terminal"

#define MyAppVersion GetEnv("PANTHA_VERSION")
#if MyAppVersion == ""
  #define MyAppVersion "v0.0.0"
#endif

[Setup]
AppId={{A7C9A8B4-0F2A-4C5D-9E2A-1A1F9B8D9C01}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=..\installer_output
OutputBaseFilename=PanthaSetup-Windows-{#MyAppVersion}

Compression=lzma
SolidCompression=yes
WizardStyle=modern

SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

WizardResizable=no
DisableProgramGroupPage=yes

PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

UsePreviousAppDir=yes
UsePreviousGroup=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; Flags: unchecked
Name: "startup"; Description: "Run Pantha Terminal when Windows starts"; Flags: unchecked

[Files]
Source: "..\dist\PanthaTerminal\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startup

[Run]
; --- BEST LAUNCH METHOD: Windows Terminal (keeps it open, shows output)
Filename: "wt.exe"; \
  Parameters: "-w 0 new-tab --title ""Pantha Terminal"" cmd /k ""cd /d """"{app}"""" && """"{app}\{#MyAppExeName}"""""""; \
  Description: "Launch {#MyAppName} (Windows Terminal)"; \
  Flags: postinstall nowait skipifsilent; \
  Check: WindowsTerminalExists

; --- FALLBACK: cmd.exe (still keeps window open)
Filename: "cmd.exe"; \
  Parameters: "/k ""cd /d """"{app}"""" && """"{app}\{#MyAppExeName}"""""""; \
  Description: "Launch {#MyAppName} (Command Prompt)"; \
  Flags: postinstall nowait skipifsilent; \
  Check: not WindowsTerminalExists

[Code]
function WindowsTerminalExists(): Boolean;
begin
  Result := FileExists(ExpandConstant('{sys}\wt.exe'));
end;
