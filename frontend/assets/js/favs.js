// نبراس — المفضلة والمراجعات المحلية (حل client-side لا يتطلب تعديل backend)
const FAVS_KEY = "nibras_favorites";
const REVIEWS_KEY = "nibras_reviews";

export const getFavs = () => {
  try { return JSON.parse(localStorage.getItem(FAVS_KEY) || "[]"); } catch { return []; }
};
export const isFav = (type, id) => getFavs().some((f) => f.type === type && String(f.id) === String(id));
export function toggleFav(type, id, title, url) {
  const favs = getFavs();
  const i = favs.findIndex((f) => f.type === type && String(f.id) === String(id));
  if (i >= 0) { favs.splice(i, 1); } else { favs.unshift({ type, id: String(id), title: String(title || "").slice(0, 120), url }); }
  localStorage.setItem(FAVS_KEY, JSON.stringify(favs));
  return i < 0;
}
export function removeFav(type, id) {
  const favs = getFavs().filter((f) => !(f.type === type && String(f.id) === String(id)));
  localStorage.setItem(FAVS_KEY, JSON.stringify(favs));
}

export const getMyReviews = () => {
  try { return JSON.parse(localStorage.getItem(REVIEWS_KEY) || "[]"); } catch { return []; }
};
export function addMyReview(entry) {
  const reviews = getMyReviews();
  reviews.unshift({ ...entry, at: new Date().toISOString() });
  localStorage.setItem(REVIEWS_KEY, JSON.stringify(reviews));
}
