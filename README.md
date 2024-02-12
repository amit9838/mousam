<div align="center">
<img src="data/icons/hicolor/scalable/apps/io.github.amit9838.mousam.svg?raw=true" width="120">
<h1>Mousam</h1>

<p>Beautiful lightweight weather app based on Python and Gtk</p>


<a href = "https://github.com/amit9838/mousam/releases"><img src="https://img.shields.io/github/v/release/amit9838/mousam?style=flat&label=Latest+Release&color=%234a92ff"></a>
<a href = "https://github.com/amit9838/mousam/discussions"><img alt="GitHub Discussions" src="https://img.shields.io/github/discussions/amit9838/mousam?logo=github&color=orange"></a>
</div>
<div align="center">
<img src="https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss2-thunderstorm.png?raw=true#gh-dark-mode-only">
<img src="https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss4-light_mode.png?raw=true#gh-light-mode-only">
</div>

## Features
* Displays real-time temperature, humidity, and wind speed,UV index,pressure and more
* Utilizes graphical representations, such as temperature , precipitation graphs and wind-speed with direction to provide an hourly forecast for the next 24 hours
* Also shows tomorrow and 7-day forcasts
* See conditions in metric or imperial systems

## Installation

### **Flatpak:**

<a href='https://flathub.org/apps/io.github.amit9838.mousam'><img width='240' alt='Download on Flathub' src='https://dl.flathub.org/assets/badges/flathub-badge-en.png'/></a>

* Or you can use the terminal:
```
flatpak install flathub io.github.amit9838.mousam
```

### **Snap:**

<a href='https://snapcraft.io/mousam'><img width='240' alt='Download on SnapCraft' src='https://github.com/snapcore/snap-store-badges/blob/master/EN/%5BEN%5D-snap-store-black-uneditable.png?raw=true'/></a>

* Or you can use the terminal:

```
sudo snap install mousam
```

## Build
### Dependances
* python3-requests
* build-essential
* meson
  
### Build
```
rm -rf builddir
meson setup -Dprefix=$HOME/.local builddir
meson compile -C builddir --verbose
```

### Install
```
meson install -C builddir
```
### Run
```
mousam
```

### **Debian** (Unofficial)
Thanks to @hsbasu for maintaining Debian package

[Installation Instruction](https://github.com/amit9838/mousam/discussions/68)



<div align="center">
 <h2>Support</h2>
I hope you ❤️ <b>Mousam</b>, if you think it is worth supporting you can do so using below methods
<br>
<br>
<a href="https://www.buymeacoffee.com/ami9838" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>
</div>
<div align="center">
<a href="https://opencollective.com/weather"><img src="https://opencollective.com/spotube/donate/button.png?color=blue" alt="Donate to our Open Collective" height="45"></a>
</div>
