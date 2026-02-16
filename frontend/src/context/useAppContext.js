import { useContext } from "react";
import AppStateContext from "./AppStateContext";

export function useAppContext() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error("useAppContext must be used within AppProvider");
  }
  return context;
}

export default useAppContext;
