import React, { createContext, useState, useContext, useCallback, useRef, useEffect } from 'react';

// ---------------------------------------------------------------------------
// View name constants — use these everywhere instead of raw strings
// ---------------------------------------------------------------------------
export const VIEW_SIMULATION   = 'SIMULATION';
export const VIEW_SWARM_3D     = 'SWARM_3D';
export const VIEW_COVERAGE_MAP = 'COVERAGE_MAP';

const ViewContext = createContext();

export const ViewProvider = ({ children }) => {
  // Primary = center-area   |   Secondary = bottom-left slot
  const [primaryView,   setPrimaryView]   = useState(VIEW_SIMULATION);
  const [secondaryView, setSecondaryViewState] = useState(VIEW_SWARM_3D);

  // Refs that always hold the latest view values so functional updaters
  // inside setPrimaryView / setSecondaryViewState never close over stale state.
  const primaryViewRef   = useRef(primaryView);
  const secondaryViewRef = useRef(secondaryView);
  useEffect(() => { primaryViewRef.current   = primaryView;   }, [primaryView]);
  useEffect(() => { secondaryViewRef.current = secondaryView; }, [secondaryView]);

  /**
   * Swap primary and secondary views with each other.
   * Derived purely from refs so the closure is always fresh.
   */
  const swapViews = useCallback(() => {
    const oldPrimary   = primaryViewRef.current;
    const oldSecondary = secondaryViewRef.current;
    setPrimaryView(oldSecondary);
    setSecondaryViewState(oldPrimary);
  }, []);  // no deps — reads current values via refs at call time

  /**
   * Change the secondary slot to `view`.
   * If `view` is already showing in the primary slot the two are swapped
   * so we never end up with the same view in both slots.
   */
  const setSecondaryView = useCallback((view) => {
    if (view === primaryViewRef.current) {
      // promote current secondary to primary to avoid duplicate
      setPrimaryView(secondaryViewRef.current);
    }
    setSecondaryViewState(view);
  }, []);  // no deps — reads current values via refs at call time

  return (
    <ViewContext.Provider value={{
      primaryView,
      secondaryView,
      swapViews,
      setSecondaryView,
    }}>
      {children}
    </ViewContext.Provider>
  );
};

export const useView = () => useContext(ViewContext);
