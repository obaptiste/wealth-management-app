'use client';

import React from 'react';
import {
  Card as ChakraCard,
  Box,
  Container,
  Flex,
  Heading,
  Text,
  Button,
  CardBody,
  SimpleGrid,
  
} from '@chakra-ui/react';
import { ThemeToggle } from '@/components/ThemeToggle';


const Card: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return (
    <Box
      borderWidth="1px"
      borderRadius="lg"
      overflow="hidden"
      boxShadow="md"
      bg="white"
      _dark={{ bg: 'gray.800' }}
    >
      {children}
    </Box>
  );
}
 const CardHeader: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return (
    <Box
      px={4}
      py={2}
      borderBottomWidth="1px"
      bg="gray.50"
      _dark={{ bg: 'gray.700' }}
    >
      {children}
    </Box>
  );
}

export default function Dashboard() {
  return (
    <Card>
    <Box minH="100vh" w="full">
      <Box as="header" py={4} px={6} borderBottomWidth="1px">
        <Flex justify="space-between" align="center" maxW="container.xl" mx="auto">
          <Heading size="lg">OpenBank Wealth Management</Heading>
          <ThemeToggle />
        </Flex>
      </Box>
      
      <Container maxW="container.xl" py={8}>
        <Heading mb={6}>Dashboard</Heading>
        
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6} mb={8}>
          <ChakraCard>
            <CardHeader>
              <Heading size="md">Portfolio Value</Heading>
            </CardHeader>
            <CardBody>
              <Heading size="xl">$234,500</Heading>
              <Text color="green.500">+5.2% today</Text>
            </CardBody>
          </ChakraCard>
          
          <ChakraCard>
            <CardHeader>
              <Heading size="md">Assets</Heading>
            </CardHeader>
            <CardBody>
              <Heading size="xl">12</Heading>
              <Text>Across 4 categories</Text>
            </CardBody>
          </ChakraCard>
          
          <ChakraCard>
            <CardHeader>
              <Heading size="md">Performance</Heading>
            </CardHeader>
            <CardBody>
              <Heading size="xl">+12.4%</Heading>
              <Text>Year to date</Text>
            </CardBody>
          </ChakraCard>
        </SimpleGrid>
        
        <Flex gap={6} flexDirection={{ base: 'column', md: 'row' }}>
          <Button colorScheme="primary" size="lg">Add Asset</Button>
          <Button colorScheme="secondary" size="lg">View Reports</Button>
        </Flex>
      </Container>
    </Box>
    </Card>
  );
}