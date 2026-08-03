# Front end changes

Five pages rewritten plus one new stylesheet. Drop these over the originals,
keeping the same folder structure.

    templates/home.html
    templates/prediction.html
    templates/result.html
    templates/aboutapp.html
    templates/dashboard.html
    static/css/theme.css        <- new file

## Why

The original pages used four unrelated colour schemes. The home page nav was
mustard `#8c851e`, the about page dark grey `#333`, the dashboard light grey
`#f5f5f5`. Nothing shared a stylesheet, so the app read as four separate
projects. None of the pages worked on a phone.

## What each file does now

**static/css/theme.css** is new and holds the whole palette in CSS variables at
the top. Change a colour there and every page follows. Primary green `#2f9e58`.
It also carries the shared navigation bar, the button style, the card style and
the mobile rules.

**home.html** was a static hero with a Get Started button. Now a landing page
with three sections: a hero, an "Empowering plant protection" band, and a
three-step How It Works row.

**prediction.html** gained a click-to-upload area with an image preview before
submission, class chips listing the seven categories, and a progress overlay.
The overlay is described below.

**result.html** restyled onto the shared theme. The three template variables it
receives are unchanged, `filename`, `prediction` and `Cure`, so `app.py` needed
no edit.

**aboutapp.html** rebuilt on the shared theme with the model and dataset
described.

**dashboard.html** had no navigation at all and its own separate styling. Now on
the shared theme, with the live sensor readings and a status line. Every element
id was preserved, so the fetch logic still targets the same nodes.

## Three specific additions worth noting in the report

**Progress overlay on inference.** Uploading a leaf gave no feedback while the
model ran, so the page looked frozen. A full screen overlay now shows a spinning
leaf and a bar filling to 95 percent while the request is in flight. It stops at
95 rather than 100 because the true completion point is the server response, and
a bar sitting at 100 percent while nothing happens is worse than one sitting at
95.

**Liveness indicator on the dashboard.** Firebase holds only the most recent
reading, so a node that stops uploading leaves a value that a naive dashboard
would present as current. The status line reports how long ago the reading
arrived and warns above 60 seconds rather than showing stale data as live.

**Responsive layout.** Text sizes use `clamp()` so they scale with viewport
width. Below 760 pixels the navigation collapses to a menu button. The original
pages had fixed pixel sizing throughout and were unusable on a phone.

## One thing left undone

`login.html` and `signup.html` were not restyled, because neither has a backend.
They are markup with no route behind them. Either finish them or remove them,
since a page that looks functional and does nothing reads worse than its
absence. Separately, `login.html` requests `/static/CSS/lsstyle.css` with a
capital directory name against a lowercase `css/` folder, which works on Windows
and fails on Linux.
