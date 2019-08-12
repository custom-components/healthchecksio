# healthchecksio

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE.md)

[![hacs][hacsbadge]](hacs)
![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

_Integration to integrate with [healthchecks.io][healthchecksio]._

**Update and display the status of your checks.**

_This will update every 5 minuttes._

Platform | Description
-- | --
`binary_sensor` | Show if the monitor has a good status or not.

![example][exampleimg]

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `healthchecksio`.
4. Download _all_ the files from the `custom_components/healthchecksio/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Healthchecks.io"

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/healthchecksio/.translations/en.json
custom_components/healthchecksio/__init__.py
custom_components/healthchecksio/binary_sensor.py
custom_components/healthchecksio/config_flow.py
custom_components/healthchecksio/const.py
custom_components/healthchecksio/manifest.json
```

## Configuration

This can **only** be configured in the UI.

### Check ID

This is the ID of the check that this integration should update, this ID looks something like `aa247c51-8da8-4800-86a3-48763142e902`

This integration will send an update to it every `5` minuttes.

### API Key

The API key to your account.
You find that under the "Settings" tab in your project.
This can **not** be the "Read only" key.


## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[healthchecksio]: https://healthchecks.io
[buymecoffee]: https://www.buymeacoffee.com/ludeeus
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/healthchecksio.svg?style=for-the-badge
[commits]: https://github.com/custom-components/healthchecksio/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/custom-components/healthchecksio.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Joakim%20Sørensen%20%40ludeeus-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/custom-components/healthchecksio.svg?style=for-the-badge
[releases]: https://github.com/custom-components/healthchecksio/releases
