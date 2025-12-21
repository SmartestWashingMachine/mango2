export const getColorForIndex = (idx: number) => {
  /*
  const hue = 287.46;
  const sat = 65.05;

  const baseLightness = 40.39;

  // The idea is that for long texts, the later texts in the image have a low change.
  // By the point the user is reading later texts, they should already be familiar with the reading order.
  const factor = Math.pow(0.8, idx);
  const lightness = baseLightness * factor;

  return `hsl(${hue}, ${sat}%, ${lightness}%)`;
  */

  const hue = (idx * 137.5) % 360;
  return `hsl(${hue}, 70%, 50%)`;
};
