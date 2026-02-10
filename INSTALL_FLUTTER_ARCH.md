# Quick Flutter Installation for Arch Linux

Since you're on Arch Linux, here's the fastest way to install Flutter:

## Option 1: Using yay (Recommended)

```bash
yay -S flutter
```

## Option 2: Using pacman

```bash
sudo pacman -S flutter
```

## Option 3: Manual Installation

```bash
# Download Flutter
cd ~
wget https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.24.5-stable.tar.xz
tar xf flutter_linux_3.24.5-stable.tar.xz

# Add to PATH (check if you use bash or zsh)
echo $SHELL

# For zsh (common on Arch)
echo 'export PATH="$HOME/flutter/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export PATH="$HOME/flutter/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
flutter --version
flutter doctor
```

## After Installation

```bash
# Check installation
flutter doctor

# Fix any issues (if Android development)
flutter doctor --android-licenses

# Navigate to mobile app
cd /home/chibionos/r/entobot/mobile/entobot_flutter

# Install dependencies
flutter pub get

# Run the app
flutter run
```

## What You'll Need

- **Android Studio** (for Android emulator): `yay -S android-studio`
- **Chrome** (for web testing): `yay -S google-chrome`
- **USB device** (for physical testing)

## Quick Test

```bash
# List available devices
flutter devices

# If no devices, create Android emulator
flutter emulators
flutter emulators --launch <emulator-id>

# Or use Chrome
flutter run -d chrome
```

## Troubleshooting

### "Flutter not found"
```bash
# Check if in PATH
which flutter

# If not, re-add to PATH
export PATH="$HOME/flutter/bin:$PATH"
```

### Android SDK issues
```bash
# Install Android SDK
yay -S android-sdk android-sdk-platform-tools

# Accept licenses
flutter doctor --android-licenses
```

### Missing dependencies
```bash
# Install common dependencies
sudo pacman -S base-devel git cmake ninja
```

---

**Recommended**: Use `yay -S flutter` for easiest installation!
