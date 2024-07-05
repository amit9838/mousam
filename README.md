<div align="center">
<img src="data/icons/hicolor/scalable/apps/io.github.amit9838.mousam.svg?raw=true" width="120">
<h1>Mousam</h1>

<p>Weather at a Glance</p>


<a href = "https://github.com/amit9838/mousam/releases"><img src="https://img.shields.io/github/v/release/amit9838/mousam?style=flat&label=Latest+Release&color=%234a92ff"></a>
<a href = "https://github.com/amit9838/mousam/discussions"><img alt="GitHub Discussions" src="https://img.shields.io/github/discussions/amit9838/mousam?logo=github&color=orange"></a>
</div>
<div align="center">
<img src="https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss5-overcast.png?raw=true#gh-dark-mode-only">
<img src="https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss4-light_mode.png?raw=true#gh-light-mode-only">
</div>

## Features
* Displays real-time temperature, humidity, wind speed, UV index, pressure and more
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
### **Debian** (Unofficial)
<a href='https://github.com/amit9838/mousam/discussions/68'><img width='240' alt='Download on SnapCraft' src='https://www.m5hosting.com/wp-content/uploads/2021/07/debian-dedicated-server.jpg' style="border-radius:5px; padding:3px 8px; background-color:white;"></a>

Thanks to @hsbasu for maintaining Debian package

[Installation Instruction](https://github.com/amit9838/mousam/discussions/68)

## Build
> [!TIP]
> To avoid headaches, you can use Nix to build and run the project with just one command. See [Use Nix](#use-nix) for more information.

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

## Use Nix
### What is Nix and why should I use it?
Nix is a package manager that is designed to work on multiple platforms. It helps to avoid dependency hell. It is a great tool for developers who want to build and run the project without worrying about the dependencies.

### How do I install Nix?
For more information, see [Nix Manual](https://nix.dev/manual/nix/2.18/installation/installation).

### How do I use Nix?
Enter the root directory of the project and run the following command:
```
nix-shell
```
This command will create a shell, which downloads and installs all dependencies needed to build and run the project. Now you can follow the [steps above](#build-1) to build, install and run the app.

> [!TIP]
> To skip the build process, you can run the following command: bash run-app

## Contribution
Thanks to all the contributors have helped in the development project so that open-source community can enjoy best tools with best features.
 

<a href="https://github.com/amit9838/mousam/graphs/contributors">
<img src="https://contrib.rocks/image?repo=amit9838/mousam&columns=10"/>
</a>




## Credits
- Thanks to [Open Meteo](https://open-meteo.com/) from providing weather data for free of cost. 

- Thanks to [@basmilius](https://github.com/basmilius) for making beautiful weather icons.

<div align="center">
 <h2>Support</h2>
I hope you ❤️ <b>Mousam</b>, if you think it is worth supporting you can do so using below methods
<br>
<br>
<a href="https://www.buymeacoffee.com/ami9838" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>
</div>
<div align="center">
</div>
