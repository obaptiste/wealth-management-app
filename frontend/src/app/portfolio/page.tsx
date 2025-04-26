//the portfolio page

import { Box, Heading, Text, SimpleGrid, Button, Progress, VStack, Card as ChakraCard, CardHeader, CardBody } from "@chakra-ui/react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { MotionDiv } from "@/components/motion-div";

const mockData = [
  { name: 'Jan', value: 4000 },
  { name: 'Feb', value: 4300 },
  { name: 'Mar', value: 4600 },
  { name: 'Apr', value: 4800 },
  { name: 'May', value: 5000 },
];

export default function PortfolioPage() {
  return (
    <MotionDiv className="p-6">
      <VStack align="start" spacing={6}>
        <Heading size="xl">My Portfolio</Heading>

        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} width="100%">
          <ChakraCard>
            <CardHeader>
              <Heading size="md">Portfolio Value</Heading>
            </CardHeader>
            <CardBody>
              <Text fontSize="2xl" fontWeight="bold">$5,000</Text>
              <Text fontSize="sm" color="gray.500" mt={2}>+5% this month</Text>
            </CardBody>
          </ChakraCard>

          <ChakraCard>
            <CardHeader>
              <Heading size="md">Cash Available</Heading>
            </CardHeader>
            <CardBody>
              <Text fontSize="2xl" fontWeight="bold">$1,200</Text>
              <Button mt={4} width="full" colorScheme="blue">Add Funds</Button>
            </CardBody>
          </ChakraCard>
        </SimpleGrid>

        <ChakraCard width="100%">
          <CardHeader>
            <Heading size="md">Portfolio Growth</Heading>
          </CardHeader>
          <CardBody>
            <Box width="100%" height="300px">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={mockData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </CardBody>
        </ChakraCard>

        <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6} width="100%">
          <ChakraCard>
            <CardHeader>
              <Heading size="sm">Stocks</Heading>
            </CardHeader>
            <CardBody>
              <Text fontSize="lg" fontWeight="bold">$3,000</Text>
              <Progress value={60} mt={2} colorScheme="green" />
            </CardBody>
          </ChakraCard>
          <ChakraCard>
            <CardHeader>
              <Heading size="sm">Crypto</Heading>
            </CardHeader>
            <CardBody>
              <Text fontSize="lg" fontWeight="bold">$1,500</Text>
              <Progress value={30} mt={2} colorScheme="purple" />
            </CardBody>
          </ChakraCard>
          <ChakraCard>
            <CardHeader>
              <Heading size="sm">Cash</Heading>
            </CardHeader>
            <CardBody>
              <Text fontSize="lg" fontWeight="bold">$500</Text>
              <Progress value={10} mt={2} colorScheme="blue" />
            </CardBody>
          </ChakraCard>
        </SimpleGrid>
      </VStack>
    </MotionDiv>
  );
}
