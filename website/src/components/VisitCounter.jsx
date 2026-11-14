// Counts visits with hitscounter.dev. The service counts every time this image is
// requested, so it is loaded once per page view. It stays hidden: open the site with
// ?visits (https://amit9838.github.io/mousam/?visits) to show the badge.
export const COUNTER_URL =
  "https://hitscounter.dev/api/hit?url=https%3A%2F%2Famit9838.github.io%2Fmousam%2F&label=Visits&icon=github&color=%23198754&message=&style=flat&tz=UTC";

export default function VisitCounter() {
  // Do not count local development or preview runs
  if (!import.meta.env.PROD) return null;

  const visible = new URLSearchParams(window.location.search).has("visits");
  return visible ? (
    <img src={COUNTER_URL} alt="Visits" />
  ) : (
    <img src={COUNTER_URL} alt="" aria-hidden="true" width="1" height="1" className="hidden" />
  );
}
