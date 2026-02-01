; --------------------------------------------------
; METADATA
; --------------------------------------------------

#define MyAppName "Pantha Terminal"
#define MyAppExeName "PanthaTerminal.exe"
#define MyAppPublisher "Pantha"
#define MyAppURL "https://github.com/V1LE-CODE/pantha-terminal"

#define RawVersion GetEnv("PANTHA_VERSION")
#if RawVersion == ""
  #define MyAppVersion "0.0.0"
#else
  #define MyAppVersion RawVersion
#endif

; --------------------------------------------------
; SETUP
; --------------------------------------------------

[Setup]
AppId={{A7C9A8B4-0F2A-4C5D-9E2A-1A1F9B8D9C01}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}

AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=..\installer_output
OutputBaseFilename=PanthaSetup-Windows-{#MyAppVersion}

SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

WizardResizable=no
DisableProgramGroupPage=yes

PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

UsePreviousAppDir=yes
UsePreviousGroup=yes

DisableDirPage=auto
DisableReadyMemo=no
DisableFinishedPage=no

CloseApplications=yes
RestartApplications=no

; --------------------------------------------------
; LANGUAGES
; --------------------------------------------------

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; --------------------------------------------------
; TASKS
; --------------------------------------------------

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; Flags: unchecked
Name: "startup"; Description: "Run Pantha Terminal when Windows starts"; Flags: unchecked

; --------------------------------------------------
; FILES
; --------------------------------------------------

; ★ ONEDIR PyInstaller output
[Files]
Source: "..\dist\PanthaTerminal\*"; \
  DestDir: "{app}"; \
  Flags: recursesubdirs createallsubdirs ignoreversion

; --------------------------------------------------
; ICONS
; --------------------------------------------------

[Icons]
Name: "{group}\{#MyAppName}"; \
  Filename: "{app}\{#MyAppExeName}"

Name: "{commondesktop}\{#MyAppName}"; \
  Filename: "{app}\{#MyAppExeName}"; \
  Tasks: desktopicon

; --------------------------------------------------
; REGISTRY (STARTUP OPTION)
; --------------------------------------------------

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; \
  ValueName: "{#MyAppName}"; \
  ValueData: """{app}\{#MyAppExeName}"""; \
  Flags: uninsdeletevalue; \
  Tasks: startup

; --------------------------------------------------
; RUN
; --------------------------------------------------

[Run]
Filename: "{app}\{#MyAppExeName}"; \
  Description: "Launch {#MyAppName}"; \
  Flags: nowait postinstall skipifsilent
