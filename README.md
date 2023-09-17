<div align="center">
<img src="data/icons/hicolor/scalable/apps/io.github.amit9838.weather.svg?raw=true" width="120">
<h1>Weather</h1>
<p>Beautiful lightweight weather app.</p>
<img src="https://img.shields.io/github/v/release/amit9838/weather?style=flat&label=Latest+Release&color=%234a92ff">
</div>
<div align="center">
<img src="https://github.com/amit9838/weather/blob/master/screenshots/ss2-haze_night.png?raw=true#gh-dark-mode-only">
<img src="https://github.com/amit9838/weather/blob/master/screenshots/ss1-overcast_clouds_day.png?raw=true#gh-light-mode-only">
</div>

## Features
* See weather with dynamically changing gradient-based background according to current weather condition
* See today, tomorrow and 5-day forcasts
* See conditions in metric or imperial systems
* Option to use Personal API Key

## Installation

### **Flatpak:**

<a href='https://flathub.org/apps/io.github.amit9838.weather'><img width='240' alt='Download on Flathub' src='https://dl.flathub.org/assets/badges/flathub-badge-en.png'/></a>

* Or you can use the terminal:
```
flatpak install flathub io.github.amit9838.weather
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
meson build
ninja -C build
```

### Install
```
sudo ninja -C build install
```
### Run
```
weather
```

