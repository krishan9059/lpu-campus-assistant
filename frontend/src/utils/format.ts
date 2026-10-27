const dateFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

export function formatDate(iso: string | null): string {
  if (!iso) return "";
  const parsed = new Date(`${iso}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? iso : dateFormatter.format(parsed);
}

export function daysUntil(iso: string): number {
  const target = new Date(`${iso}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / 86_400_000);
}

export function formatDeadline(iso: string): string {
  const days = daysUntil(iso);
  if (days < 0) return "Registration closed";
  if (days === 0) return "Closes today";
  if (days === 1) return "Closes tomorrow";
  return `Closes in ${days} days`;
}

export function formatCtc(lpa: number): string {
  return `${lpa % 1 === 0 ? lpa.toFixed(0) : lpa.toFixed(1)} LPA`;
}

const CATEGORY_LABELS: Record<string, string> = {
  regular: "Regular",
  dream: "Dream",
  super_dream: "Super Dream",
};

export function formatCategory(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}
