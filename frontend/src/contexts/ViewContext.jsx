import React, { createContext, useState, useContext, useCallback } from 'react';

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

  /**
   * Swap primary and secondary views with each other.
   */
  const swapViews = useCallback(() => {
    setPrimaryView(prev => {
      setSecondaryViewState(prev);   // secondary becomes old primary
      return secondaryView;          // primary becomes old secondary
    });
  }, [secondaryView]);

  /**
   * Change the secondary slot to `view`.
   * If `view` is already showing in the primary slot the two are swapped
   * so we never end up with the same view in both slots.
   */
  const setSecondaryView = useCallback((view) => {
    if (view === primaryView) {
      // promote current secondary to primary to avoid duplicate
      setPrimaryView(secondaryView);
    }
    setSecondaryViewState(view);
  }, [primaryView, secondaryView]);

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
