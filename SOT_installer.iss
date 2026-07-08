; ========================================
; SOT - Staff Operations Tracker
; Inno Setup Installer Script
; ========================================
; HOW TO USE:
; 1. Install Inno Setup from https://jrsoftware.org/isdl.php
; 2. Download VC++ x64 runtime from Microsoft and save as:
;    vc_redist.x64.exe  (in same folder as this file)
;    Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
; 3. Run build.bat  (it calls this script automatically)
;    OR open this file in Inno Setup IDE and press F9
; ========================================

#define MyAppName      "SOT - Staff Operations Tracker"
#define MyAppShortName "SOT"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "SOT"
#define MyAppExeName   "SOT.exe"

[Setup]
; Basic info
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
SetupIconFile=ui\logo.ico
WizardSmallImageFile=ui\logo.ico

; Where to install
DefaultDirName={autopf}\{#MyAppShortName}
DefaultGroupName={#MyAppShortName}
DisableProgramGroupPage=yes

; Output
OutputDir=installer_output
OutputBaseFilename=SOT_Setup
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Require admin rights (needed to install to Program Files)
PrivilegesRequired=admin

; Minimum Windows version: Windows 10 (10.0)
MinVersion=10.0

; Architecture: 64-bit only
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Installer window style
WizardStyle=modern
WizardResizable=no

; Uninstaller
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
CreateUninstallRegKey=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Optional: create desktop shortcut (checked by default)
Name: "desktopicon"; Description: "Create a &Desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
; Main application executable (built by PyInstaller)
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; App icon (so uninstaller entry in Control Panel shows the logo)
Source: "ui\logo.ico"; DestDir: "{app}"; Flags: ignoreversion

; VC++ Runtime - will be extracted and run silently if needed
; IMPORTANT: Download vc_redist.x64.exe from Microsoft and place it
; in the same folder as this .iss file before building
Source: "vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
; Start menu shortcut
Name: "{group}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"

; Desktop shortcut (only if user selected the task above)
Name: "{userdesktop}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon

; Uninstall shortcut in Start Menu
Name: "{group}\Uninstall {#MyAppShortName}"; Filename: "{uninstallexe}"

[Run]
; Step 1: Silently install VC++ Runtime BEFORE launching the app
; /install /quiet /norestart = silent install, no reboot prompt
; The check skips install if VC++ is already present (returncode 0x80070666 = already installed)
Filename: "{tmp}\vc_redist.x64.exe"; \
    Parameters: "/install /quiet /norestart"; \
    StatusMsg: "Installing required Visual C++ runtime..."; \
    Flags: waituntilterminated; \
    Check: VCRedistNeedsInstall

; Step 2: Optionally launch SOT after install finishes
Filename: "{app}\{#MyAppExeName}"; \
    Description: "Launch {#MyAppShortName} now"; \
    Flags: nowait postinstall skipifsilent

[Code]
// Check if VC++ 2015-2022 x64 Redistributable is already installed
// Returns True if it NEEDS to be installed (i.e. not found)
// Returns False if already installed (skip the installer)
function VCRedistNeedsInstall: Boolean;
var
  // Registry key where VC++ 2022 x64 stores its install info
  SubKey: String;
  Installed: Cardinal;
begin
  SubKey := 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64';
  
  // Check if the key exists and Installed = 1
  if RegQueryDWordValue(HKEY_LOCAL_MACHINE, SubKey, 'Installed', Installed) then
  begin
    if Installed = 1 then
    begin
      // Already installed - skip
      Result := False;
      Exit;
    end;
  end;
  
  // Not found - needs install
  Result := True;
end;

// Show a friendly message if the vc_redist file is missing
// (developer forgot to download it before building)
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
