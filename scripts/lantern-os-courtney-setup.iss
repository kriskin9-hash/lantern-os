; Lantern OS Courtney Installer
; Inno Setup script for creating a Windows EXE installer

[Setup]
AppName=Lantern OS for Courtney
AppVersion=1.0.0
DefaultDirName={userdocs}\Lantern-OS
DefaultGroupName=Lantern OS
OutputBaseFilename=Lantern-OS-Courtney-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\lantern-icon.ico

[Files]
; Copy the setup wizard
Source: "scripts\Invoke-CourtneySetupWizard.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "docs\COURTNEY-QUICK-SYNC-2026-05-30.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "docs\COURTNEY-DESKTOP-BRIDGE-SETUP-2026-05-30.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Lantern OS Setup"; Filename: "{app}\Invoke-CourtneySetupWizard.ps1"
Name: "{commondesktop}\Lantern OS Setup"; Filename: "{app}\Invoke-CourtneySetupWizard.ps1"

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\Invoke-CourtneySetupWizard.ps1"""; Description: "Run Lantern OS Setup Wizard"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel1=Welcome to the Lantern OS Setup Wizard
WelcomeLabel2=This will install Lantern OS for Courtney on your computer.%n%n%nLantern OS requires Node.js, Python, and Git to be installed first.
