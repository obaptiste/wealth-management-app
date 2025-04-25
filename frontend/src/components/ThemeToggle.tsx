// src/components/ThemeToggle.tsx (or similar)
'use client';

import * as React from 'react';
import { IconButton } from '@chakra-ui/react';
import { 
  Tooltip as ChakraTooltip, 
   
  TooltipProps as ChakraTooltipProps 
} from '@chakra-ui/react';
import { useColorMode } from '@chakra-ui/color-mode';
import { FiMoon, FiSun } from 'react-icons/fi';

export interface TooltipProps extends ChakraTooltipProps {
  showArrow?: boolean
  portalled?: boolean
  portalRef?: React.RefObject<HTMLElement>
  tooltipContent: React.ReactNode
  disabled?: boolean
}

export const Tooltip = React.forwardRef<HTMLDivElement, TooltipProps>(
  function Tooltip(props, ref) {  
    const { 
      showArrow, 
      portalled, portalRef, tooltipContent, 
      children, disabled, ...rest } = props;

      if (disabled) return children;

    return (
      <ChakraTooltip
        ref={ref}
        label={tooltipContent}
        hasArrow={showArrow}
        placement="bottom"
        portalProps={portalled ? { containerRef: portalRef } : undefined}
        {...rest}
      >
        {children}
      </ChakraTooltip>
    )
  },
)


export function ThemeToggle() {
  const { colorMode, toggleColorMode } = useColorMode();

  const tooltipLabel = colorMode === 'light' ? 'Switch to dark mode' : 'Switch to light mode';

  return (
    <Tooltip tooltipContent={tooltipLabel} showArrow>
      <IconButton
        aria-label={`Toggle ${colorMode === 'light' ? 'Dark' : 'Light'} Mode`}
        onClick={toggleColorMode}
        variant="ghost"
        colorScheme="gray"
        size="md"
        as={colorMode === 'light' ? FiMoon : FiSun}
      />
    </Tooltip>
  );
}