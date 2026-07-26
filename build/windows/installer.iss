; installer.iss — Inno Setup script.
; Compiled with the Inno Setup Compiler (ISCC.exe) against the PyInstaller
; output in dist/Alfred/. Produces a double-click Setup.exe with a Start
; Menu shortcut, an uninstaller, and no admin rights required
; (installs to the current user's AppData, not Program Files).

#define MyAppName "Alfred"
#define MyAppVersion "0.1.0"
#define MyAppExeName "Alfred.exe"

[Setup]
AppId={{B9E1E9B0-6C1B-4E9A-9C9C-ALFRED00001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputDir=..\..\dist_installers
OutputBaseFilename=Alfred-Setup-{#MyAppVersion}-win
Compression=lzma2
SolidCompression=yes
DisableProgramGroupPage=yes
#ifexist "..\icon.ico"
SetupIconFile=..\icon.ico
#endif

[Files]
Source: "..\..\dist\Alfred\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent

[Code]
// Warn (but don't block) if Ollama doesn't appear to be installed, since
// Alfred needs it to actually talk to a model.
function InitializeSetup(): Boolean;
begin
  if not FileExists(ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe'))
     and not FileExists('C:\Program Files\Ollama\ollama.exe') then
  begin
    MsgBox('Alfred needs Ollama (the local model runner) to work. ' +
           'If you have not installed it yet, grab it from https://ollama.com ' +
           'before or after this installer finishes.', mbInformation, MB_OK);
  end;
  Result := True;
end;
