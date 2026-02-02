#define MyAppName "Pantha Terminal"
#define MyAppExeName "PanthaTerminal.exe"
#define MyAppPublisher "Pantha"
#define MyAppURL "https://github.com/V1LE-CODE/pantha-terminal"

#define MyAppVersion GetEnv("PANTHA_VERSION")
#if MyAppVersion == ""
  #define MyAppVersion "v0.0.0"
#endif

[Setup]
AppId={{A7C9A8B4-0F2A-4C5D-9E2A-1A1F9B8D9C01}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; ⚠️ IMPORTANT: avoid Program Files with lowest privilege
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=..\installer_output
OutputBaseFilename=PanthaSetup-Windows-{#MyAppVersion}

Compression=lzma
SolidCompression=yes
WizardStyle=modern

SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

DisableProgramGroupPage=yes
UsePreviousAppDir=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; Flags: unchecked
Name: "startup"; Description: "Run Pantha Terminal when Windows starts"; Flags: unchecked

[Files]
; ✅ COPY ENTIRE ONEDIR OUTPUT (EXE + _internal)
Source: "..\dist\PanthaTerminal\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

; 🔒 FAIL INSTALL IF EXE IS MISSING
Source: "..\dist\PanthaTerminal\PanthaTerminal.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#MyAppName}"; \
  ValueData: "{app}\{#MyAppExeName}"; \
  Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent
