#define MyAppName "Pantha Terminal"
#define MyAppExeName "PanthaTerminal.exe"
#define MyAppPublisher "Pantha"
#define MyAppURL "https://github.com/V1LE-FARM/pantha-terminal"

; Version injected by GitHub Actions (fallback if missing)
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

; ICONS / LOOK
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

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; Flags: unchecked
Name: "startup"; Description: "Run Pantha Terminal when Windows starts"; Flags: unchecked
Name: "addtopath"; Description: "Add Pantha Terminal to PATH (recommended)"; Flags: unchecked

[Files]
; Install the whole PyInstaller output folder (exe + _internal)
Source: "..\dist\PanthaTerminal\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Startup option
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startup

; Add to PATH (system PATH because installer runs as admin)
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
  ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; \
  Flags: preservestringtype; Tasks: addtopath

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeWizard();
begin
  { background }
  WizardForm.Color := $07000F;
  WizardForm.Font.Color := clWhite;

  { labels }
  WizardForm.WelcomeLabel1.Font.Color := $FF4DFF;
  WizardForm.WelcomeLabel2.Font.Color := $B066FF;

  WizardForm.PageNameLabel.Font.Color := $FF4DFF;
  WizardForm.PageDescriptionLabel.Font.Color := $B066FF;

  { buttons }
  WizardForm.NextButton.Font.Color := clWhite;
  WizardForm.BackButton.Font.Color := clWhite;
  WizardForm.CancelButton.Font.Color := clWhite;

  WizardForm.NextButton.Color := $2A003D;
  WizardForm.BackButton.Color := $2A003D;
  WizardForm.CancelButton.Color := $2A003D;
end;
