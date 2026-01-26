#define MyAppName "Pantha Terminal"
#define MyAppExeName "PanthaTerminal.exe"
#define MyAppPublisher "Pantha"
#define MyAppURL "https://github.com/V1LE-FARM/pantha-terminal"

; Version will be injected by GitHub Actions:
#define MyAppVersion GetEnv("PANTHA_VERSION")

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
DisableWelcomePage=no
DisableDirPage=no
DisableReadyMemo=no

PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

UsePreviousAppDir=yes
UsePreviousGroup=yes

; IMPORTANT: ensures installer runs from its own folder correctly
ChangesAssociations=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; Flags: unchecked
Name: "startup"; Description: "Run Pantha Terminal when Windows starts"; Flags: unchecked

[Files]
; Install the entire folder build (PanthaTerminal.exe + _internal + all bundled deps)
Source: "..\dist\PanthaTerminal\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

; OPTIONAL (recommended): include your icon in install folder too
Source: "..\assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
; Startup option
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startup

[Run]
; Launch after install
Filename: "{app}\{#MyAppExeName}";
Description: "Launch {#MyAppName}";
WorkingDir: "{app}";
Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeWizard();
begin
  WizardForm.Color := $07000F;  { deep purple-black }
  WizardForm.Font.Color := clWhite;

  WizardForm.WelcomeLabel1.Font.Color := $FF4DFF;
  WizardForm.WelcomeLabel2.Font.Color := $B066FF;

  WizardForm.PageNameLabel.Font.Color := $FF4DFF;
  WizardForm.PageDescriptionLabel.Font.Color := $B066FF;

  WizardForm.NextButton.Font.Color := clWhite;
  WizardForm.BackButton.Font.Color := clWhite;
  WizardForm.CancelButton.Font.Color := clWhite;

  WizardForm.NextButton.Color := $2A003D;
  WizardForm.BackButton.Color := $2A003D;
  WizardForm.CancelButton.Color := $2A003D;
end;
