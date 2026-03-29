"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Input,
  Card,
  CardBody,
  CardHeader,
  Grid,
  GridItem,
  useColorModeValue,
  Icon,
  FormControl,
  FormLabel,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import {
  TbPigMoney,
  TbTrendingUp,
  TbCalendar,
  TbCoin,
  TbReceipt,
} from "react-icons/tb";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiClient } from "@/lib/api";

const MotionBox = motion(Box);
const MotionCard = motion(Card);

interface PensionProjection {
  age: number;
  year: number;
  total_contributions: number;
  investment_returns: number;
  total_value: number;
}

interface CalculationResult {
  retirement_age: number;
  years_to_retirement: number;
  total_contributions: number;
  projected_value: number;
  monthly_retirement_income: number;
  projections: PensionProjection[];
}

export default function PensionPage() {
  const [currentAge, setCurrentAge] = useState("30");
  const [retirementAge, setRetirementAge] = useState("65");
  const [monthlyContribution, setMonthlyContribution] = useState("500");
  const [currentSavings, setCurrentSavings] = useState("10000");
  const [expectedReturn, setExpectedReturn] = useState(7);
  const [result, setResult] = useState<CalculationResult | null>(null);

  const bgGradient = useColorModeValue(
    "linear(to-br, accent.50, brand.50, slate.100)",
    "linear(to-br, slate.900, accent.900, brand.900)",
  );

  const cardBg = useColorModeValue("white", "slate.800");
  const accentColor = useColorModeValue("brand.500", "brand.400");
  const summaryGradient = useColorModeValue(
    "linear(to-br, brand.500, accent.500)",
    "linear(to-br, brand.600, accent.600)",
  );
  const tooltipBg = useColorModeValue("#fff", "#1E293B");
  const tableHoverBg = useColorModeValue("slate.50", "slate.700");

  const calculateProjection = useCallback(async () => {
    try {
      const response = await apiClient.calculatePensionProjection({
        currentAge: parseInt(currentAge, 10),
        retirementAge: parseInt(retirementAge, 10),
        monthlyContribution: parseFloat(monthlyContribution),
        currentSavings: parseFloat(currentSavings),
        expectedReturn,
      });
      setResult(response);
    } catch (error) {
      console.error("Error calculating projection:", error);
    }
  }, [
    currentAge,
    currentSavings,
    expectedReturn,
    monthlyContribution,
    retirementAge,
  ]);

  useEffect(() => {
    if (
      currentAge &&
      retirementAge &&
      monthlyContribution &&
      currentSavings &&
      parseInt(retirementAge) > parseInt(currentAge)
    ) {
      calculateProjection();
    }
  }, [
    calculateProjection,
    currentAge,
    retirementAge,
    monthlyContribution,
    currentSavings,
    expectedReturn,
  ]);

  const chartData =
    result?.projections.map((p) => ({
      age: p.age,
      value: p.total_value,
      contributions: p.total_contributions,
      returns: p.investment_returns,
    })) || [];

  return (
    <Box minH="100vh" bgGradient={bgGradient} py={8}>
      <Container maxW="container.xl">
        {/* Header */}
        <MotionBox
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <VStack spacing={2} align="start" mb={8}>
            <HStack spacing={3}>
              <Icon as={TbPigMoney} boxSize={10} color={accentColor} />
              <Heading
                size="2xl"
                bgGradient={`linear(to-r, ${accentColor}, accent.500)`}
                bgClip="text"
                fontWeight="800"
              >
                Pension Planning
              </Heading>
            </HStack>
            <Text fontSize="lg" color="text-secondary">
              Plan your retirement and visualize your pension growth
            </Text>
          </VStack>
        </MotionBox>

        <Grid templateColumns={{ base: "1fr", lg: "1fr 2fr" }} gap={6}>
          {/* Input Form */}
          <GridItem>
            <MotionCard
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              bg={cardBg}
              shadow="2xl"
            >
              <CardHeader>
                <Heading size="md">Your Details</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <FormControl>
                    <FormLabel fontWeight="600">Current Age</FormLabel>
                    <Input
                      type="number"
                      value={currentAge}
                      onChange={(e) => setCurrentAge(e.target.value)}
                      placeholder="Enter your age"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">
                      Target Retirement Age
                    </FormLabel>
                    <Input
                      type="number"
                      value={retirementAge}
                      onChange={(e) => setRetirementAge(e.target.value)}
                      placeholder="65"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">
                      Monthly Contribution ($)
                    </FormLabel>
                    <Input
                      type="number"
                      value={monthlyContribution}
                      onChange={(e) => setMonthlyContribution(e.target.value)}
                      placeholder="500"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">Current Savings ($)</FormLabel>
                    <Input
                      type="number"
                      value={currentSavings}
                      onChange={(e) => setCurrentSavings(e.target.value)}
                      placeholder="10000"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">
                      Expected Annual Return: {expectedReturn}%
                    </FormLabel>
                    <Slider
                      value={expectedReturn}
                      onChange={setExpectedReturn}
                      min={1}
                      max={15}
                      step={0.5}
                      colorScheme="brand"
                    >
                      <SliderTrack>
                        <SliderFilledTrack />
                      </SliderTrack>
                      <SliderThumb boxSize={6} />
                    </Slider>
                    <HStack justify="space-between" mt={2}>
                      <Text fontSize="xs" color="text-muted">
                        Conservative (1%)
                      </Text>
                      <Text fontSize="xs" color="text-muted">
                        Aggressive (15%)
                      </Text>
                    </HStack>
                  </FormControl>

                  {result && (
                    <MotionBox
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      p={6}
                      borderRadius="xl"
                      bgGradient={summaryGradient}
                      color="white"
                    >
                      <VStack spacing={3} align="stretch">
                        <HStack justify="space-between">
                          <Icon as={TbCalendar} boxSize={6} />
                          <Text fontSize="sm" fontWeight="600">
                            Years to Retirement
                          </Text>
                          <Text fontSize="2xl" fontWeight="800">
                            {result.years_to_retirement}
                          </Text>
                        </HStack>
                        <HStack justify="space-between">
                          <Icon as={TbTrendingUp} boxSize={6} />
                          <Text fontSize="sm" fontWeight="600">
                            Projected Value
                          </Text>
                          <Text fontSize="2xl" fontWeight="800">
                            ${(result.projected_value / 1000).toFixed(0)}K
                          </Text>
                        </HStack>
                        <HStack justify="space-between">
                          <Icon as={TbReceipt} boxSize={6} />
                          <Text fontSize="sm" fontWeight="600">
                            Monthly Income
                          </Text>
                          <Text fontSize="2xl" fontWeight="800">
                            ${result.monthly_retirement_income.toFixed(0)}
                          </Text>
                        </HStack>
                      </VStack>
                    </MotionBox>
                  )}
                </VStack>
              </CardBody>
            </MotionCard>
          </GridItem>

          {/* Projections Display */}
          <GridItem>
            <VStack spacing={6} align="stretch">
              {/* Stats Cards */}
              {result && (
                <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                  <MotionCard
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.1 }}
                    bg={cardBg}
                  >
                    <CardBody>
                      <Stat>
                        <StatLabel fontSize="sm" color="text-muted">
                          Total Contributions
                        </StatLabel>
                        <StatNumber fontSize="2xl" color={accentColor}>
                          ${(result.total_contributions / 1000).toFixed(0)}K
                        </StatNumber>
                        <StatHelpText>
                          <Icon as={TbCoin} mr={1} />
                          Over {result.years_to_retirement} years
                        </StatHelpText>
                      </Stat>
                    </CardBody>
                  </MotionCard>

                  <MotionCard
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.2 }}
                    bg={cardBg}
                  >
                    <CardBody>
                      <Stat>
                        <StatLabel fontSize="sm" color="text-muted">
                          Investment Returns
                        </StatLabel>
                        <StatNumber fontSize="2xl" color="accent.500">
                          $
                          {(
                            (result.projected_value -
                              result.total_contributions) /
                            1000
                          ).toFixed(0)}
                          K
                        </StatNumber>
                        <StatHelpText>
                          <Icon as={TbTrendingUp} mr={1} />
                          At {expectedReturn}% annual return
                        </StatHelpText>
                      </Stat>
                    </CardBody>
                  </MotionCard>

                  <MotionCard
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.3 }}
                    bg={cardBg}
                  >
                    <CardBody>
                      <Stat>
                        <StatLabel fontSize="sm" color="text-muted">
                          Retirement at Age
                        </StatLabel>
                        <StatNumber fontSize="2xl" color="brand.500">
                          {result.retirement_age}
                        </StatNumber>
                        <StatHelpText>
                          <Icon as={TbCalendar} mr={1} />
                          In {result.years_to_retirement} years
                        </StatHelpText>
                      </Stat>
                    </CardBody>
                  </MotionCard>
                </SimpleGrid>
              )}

              {/* Chart */}
              {result && chartData.length > 0 && (
                <MotionCard
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                  bg={cardBg}
                  shadow="2xl"
                >
                  <CardHeader>
                    <HStack justify="space-between">
                      <Heading size="md">Growth Projection</Heading>
                      <HStack spacing={4}>
                        <HStack spacing={2}>
                          <Box w={3} h={3} borderRadius="full" bg="brand.500" />
                          <Text fontSize="sm">Total Value</Text>
                        </HStack>
                        <HStack spacing={2}>
                          <Box
                            w={3}
                            h={3}
                            borderRadius="full"
                            bg="accent.500"
                          />
                          <Text fontSize="sm">Contributions</Text>
                        </HStack>
                      </HStack>
                    </HStack>
                  </CardHeader>
                  <CardBody>
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient
                            id="colorValue"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="5%"
                              stopColor="#00AC74"
                              stopOpacity={0.3}
                            />
                            <stop
                              offset="95%"
                              stopColor="#00AC74"
                              stopOpacity={0}
                            />
                          </linearGradient>
                          <linearGradient
                            id="colorContributions"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="5%"
                              stopColor="#FFB200"
                              stopOpacity={0.3}
                            />
                            <stop
                              offset="95%"
                              stopColor="#FFB200"
                              stopOpacity={0}
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                        <XAxis dataKey="age" stroke="#888" />
                        <YAxis
                          stroke="#888"
                          tickFormatter={(value) =>
                            `$${(value / 1000).toFixed(0)}K`
                          }
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: tooltipBg,
                            border: "1px solid #00AC74",
                            borderRadius: "8px",
                          }}
                          formatter={(value: number) =>
                            `$${value.toLocaleString()}`
                          }
                        />
                        <Area
                          type="monotone"
                          dataKey="value"
                          stroke="#00AC74"
                          strokeWidth={3}
                          fillOpacity={1}
                          fill="url(#colorValue)"
                        />
                        <Area
                          type="monotone"
                          dataKey="contributions"
                          stroke="#FFB200"
                          strokeWidth={2}
                          fillOpacity={1}
                          fill="url(#colorContributions)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardBody>
                </MotionCard>
              )}

              {/* Projection Table */}
              {result && (
                <MotionCard
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.5 }}
                  bg={cardBg}
                  shadow="xl"
                >
                  <CardHeader>
                    <Heading size="md">Year-by-Year Breakdown</Heading>
                  </CardHeader>
                  <CardBody maxH="400px" overflowY="auto">
                    <Table variant="simple" size="sm">
                      <Thead position="sticky" top={0} bg={cardBg} zIndex={1}>
                        <Tr>
                          <Th>Age</Th>
                          <Th isNumeric>Total Value</Th>
                          <Th isNumeric>Contributions</Th>
                          <Th isNumeric>Returns</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {result.projections
                          .filter(
                            (_, index) =>
                              index % 5 === 0 ||
                              index === result.projections.length - 1,
                          )
                          .map((projection) => (
                            <Tr
                              key={projection.age}
                              _hover={{ bg: tableHoverBg }}
                            >
                              <Td fontWeight="600">{projection.age}</Td>
                              <Td isNumeric fontWeight="700" color="brand.500">
                                ${projection.total_value.toLocaleString()}
                              </Td>
                              <Td isNumeric color="accent.500">
                                $
                                {projection.total_contributions.toLocaleString()}
                              </Td>
                              <Td isNumeric color="text-secondary">
                                $
                                {projection.investment_returns.toLocaleString()}
                              </Td>
                            </Tr>
                          ))}
                      </Tbody>
                    </Table>
                  </CardBody>
                </MotionCard>
              )}
            </VStack>
          </GridItem>
        </Grid>
      </Container>
    </Box>
  );
}
