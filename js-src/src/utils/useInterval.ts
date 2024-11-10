import { useRef, useEffect } from "react";

// CBA to remake it. From: https://www.geeksforgeeks.org/reactjs-useinterval-custom-hook/
export function useInterval(callback: any, delay: number | null) {
  const savedCallback = useRef<any>();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    function func() {
      savedCallback.current();
    }

    if (delay !== null) {
      let id = setInterval(func, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}
