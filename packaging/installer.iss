; Instalador de FT Markdown (Inno Setup 6).
; Se compila desde scripts/build.ps1, que pasa la version con /DAppVersion=x.y.z.
; Instalacion por usuario: no pide permisos de administrador (Constitucion P12).

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "FT Markdown"
#define AppExe "FT Markdown.exe"

[Setup]
; AppId identifica la aplicacion para siempre: NO cambiarlo, o las actualizaciones
; dejaran de reconocer la instalacion previa.
AppId={{F0281C15-89D1-4A34-B9CA-6F6A79956473}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=FungaTec
AppPublisherURL=https://github.com/fungatec/ft-markdown
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
LicenseFile=..\LICENSE
OutputDir=..\dist-installer
OutputBaseFilename=FT-Markdown-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExe}
CloseApplications=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#AppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; Los datos del usuario (%APPDATA%\FT Markdown) NO se borran al desinstalar (P12).
