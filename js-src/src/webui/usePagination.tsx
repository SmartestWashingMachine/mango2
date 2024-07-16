import React, { useState } from "react";

const usePagination = () => {
  const [vis, setVis] = useState<string | number>(1); // UI page number. Pages start at 1.
  const [page, setPage] = useState(0); // True page number.

  const changePage = (
    newValue: string | number,
    usingVis = true,
    max = 1,
    min = 0
  ) => {
    if (!usingVis && typeof newValue !== "number") {
      throw Error("Bad page args.");
    }

    if (usingVis) setVis(usingVis ? newValue : (newValue as number) + 1);

    const pg: number = parseInt(newValue as string, 10);
    if (Number.isNaN(pg) || !Number.isInteger(pg)) {
      return;
    }

    const truePg = usingVis ? pg - 1 : pg;
    if (truePg >= max || truePg < min) return;
    setPage(truePg);

    if (!usingVis) setVis(usingVis ? newValue : (newValue as number) + 1);

    return true;
  };

  const onChange = (e: any, max: number) => {
    const newValue = e.target.value;
    changePage(newValue, true, max);
  };

  return [vis, page, changePage, onChange] as const;
};

export default usePagination;
