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

![example][exampleimg]

## Installation

Search for and install `healthchecksio` from [HACS](https://hacs.xyz/)

## Configuration

This integration can **only** be configured via the UI.

### Check ID

This is the ID of the check that the integration should update. It looks something like `aa247c51-8da8-4800-86a3-48763142e902`.

### What the integration does

- Pings the specified Healthchecks.io check every 5 minutes to monitor the state of Home Assistant.
- Pulls your other Healthchecks.io checks as entities, so you can monitor their statuses directly in Home Assistant.

### API Key

The API key to your account. You can find it under the "Settings" tab in your project.

> [!NOTE]
> A **Full Access** API key is required for this integration to function correctly. This is because the integration both pings checks (which requires write access) and reads the status of all your checks to create entities in Home Assistant (which requires read access). Only the Full Access key provides both permissions needed for these operations.


## For self-hosted instances

### Site Root

This is the root URL of your Healthchecks.io instance.

### Ping Endpoint

This is the path of the endpoint used for pings.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Analytics

If you are using this integration, please consider enabling [Home Assistant usage analytics](https://www.home-assistant.io/integrations/analytics/#usage-analytics).

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
