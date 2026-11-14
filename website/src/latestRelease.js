// The latest published release of Mousam, read from the GitHub API, so the website
// never needs editing when a new version comes out.
const API_URL = "https://api.github.com/repos/amit9838/mousam/releases/latest";
const CACHE_KEY = "mousam-latest-release";

export const RELEASES_URL = "https://github.com/amit9838/mousam/releases";
// GitHub allows 60 anonymous requests per hour for each IP address, so ask at most once an hour
export const CACHE_MS = 60 * 60 * 1000;

// "v2.0.2" -> "2.0.2". Anything that does not look like a version is ignored.
export function versionFromTag(tag) {
  const version = String(tag ?? "").replace(/^v/i, "");
  return /^\d+(\.\d+)*$/.test(version) ? version : null;
}

// The release saved by an earlier visit: { version, url, time }, or null
export function cachedRelease() {
  try {
    const saved = JSON.parse(localStorage.getItem(CACHE_KEY));
    return saved && versionFromTag(saved.version) && saved.url ? saved : null;
  } catch {
    return null;
  }
}

// Fetch the latest release: { version, url, time }, or null when it cannot be read
export async function fetchLatestRelease(signal) {
  try {
    const response = await fetch(API_URL, {
      headers: { Accept: "application/vnd.github+json" },
      signal,
    });
    if (!response.ok) return null;
    const data = await response.json();
    const version = versionFromTag(data.tag_name);
    if (!version || typeof data.html_url !== "string") return null;
    const release = { version, url: data.html_url, time: Date.now() };
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(release));
    } catch {
      // Storage can be unavailable (private browsing); the answer is just not kept
    }
    return release;
  } catch {
    return null;
  }
}
