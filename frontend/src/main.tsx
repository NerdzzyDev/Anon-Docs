import React from "react";
import { createRoot } from "react-dom/client";
import { ChakraProvider, extendTheme } from "@chakra-ui/react";
import App from "./App";
import "./styles/globals.css";

const theme = extendTheme({
  fonts: {
    heading: "Sora, sans-serif",
    body: "Manrope, system-ui, sans-serif",
  },
  colors: {
    brand: {
      50: "#eff4ff",
      100: "#dbe8ff",
      200: "#bdd3ff",
      300: "#94b6ff",
      400: "#5d8cff",
      500: "#2f5bea",
      600: "#2448c6",
      700: "#1f3b9d",
    },
    steel: {
      50: "#f7f9fc",
      100: "#eef2f8",
      200: "#dee5f0",
      300: "#c7d2e5",
      400: "#9fb1d1",
      500: "#6e86b5",
    },
  },
  styles: {
    global: {
      "::selection": {
        background: "#cfe2ff",
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        borderRadius: "14px",
        fontWeight: 600,
      },
    },
    Checkbox: {
      baseStyle: {
        control: {
          borderRadius: "6px",
          borderColor: "steel.300",
          _checked: {
            bg: "brand.500",
            borderColor: "brand.500",
          },
          _hover: {
            borderColor: "brand.400",
          },
        },
      },
    },
    Switch: {
      baseStyle: {
        track: {
          borderRadius: "999px",
          bg: "steel.200",
          _checked: { bg: "brand.500" },
        },
      },
    },
    Input: {
      baseStyle: {
        field: {
          borderRadius: "14px",
          borderColor: "steel.200",
          _focusVisible: { borderColor: "brand.400", boxShadow: "0 0 0 3px rgba(47, 91, 234, 0.18)" },
        },
      },
    },
    Textarea: {
      baseStyle: {
        borderRadius: "14px",
        borderColor: "steel.200",
        _focusVisible: { borderColor: "brand.400", boxShadow: "0 0 0 3px rgba(47, 91, 234, 0.18)" },
      },
    },
  },
});

const container = document.getElementById("root");
if (!container) throw new Error("Root element not found");

createRoot(container).render(
  <React.StrictMode>
    <ChakraProvider theme={theme}>
      <App />
    </ChakraProvider>
  </React.StrictMode>,
);
