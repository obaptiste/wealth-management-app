'use client';

import React, { useState } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Input,
  Select,
  Button,
  Card,
  CardBody,
  CardHeader,
  Grid,
  GridItem,
  Badge,
  useColorModeValue,
  Icon,
  Flex,
  Progress,
  Switch,
  FormControl,
  FormLabel,
  SimpleGrid,
  Divider,
} from '@chakra-ui/react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TbShield,
  TbHeartbeat,
  TbUsers,
  TbTrendingUp,
  TbCoin,
} from 'react-icons/tb';
import { apiClient } from '@/lib/api';

const MotionBox = motion(Box);
const MotionCard = motion(Card);

interface InsuranceProduct {
  id: number;
  name: string;
  type: string;
  description: string;
  coverage_amount: number;
  monthly_premium: number;
  min_age: number;
  max_age: number;
}

interface Recommendation {
  product: InsuranceProduct;
  score: number;
  reason: string;
}

export default function InsurancePage() {
  const [age, setAge] = useState('30');
  const [income, setIncome] = useState('60000');
  const [dependents, setDependents] = useState('1');
  const [hasHealthInsurance, setHasHealthInsurance] = useState(false);
  const [hasLifeInsurance, setHasLifeInsurance] = useState(false);
  const [riskTolerance, setRiskTolerance] = useState('medium');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCoverage, setTotalCoverage] = useState(0);
  const [totalPremium, setTotalPremium] = useState(0);

  const bgGradient = useColorModeValue(
    'linear(to-br, brand.50, slate.100, accent.50)',
    'linear(to-br, slate.900, brand.900, slate.800)'
  );

  const cardBg = useColorModeValue('white', 'slate.800');
  const accentColor = useColorModeValue('brand.500', 'brand.400');
  const summaryBg = useColorModeValue('brand.50', 'brand.900');
  const recommendationBg = useColorModeValue('slate.50', 'slate.700');

  const getRecommendations = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getInsuranceRecommendations({
        age: parseInt(age),
        income: parseFloat(income),
        dependents: parseInt(dependents),
        hasHealthInsurance: hasHealthInsurance,
        hasLifeInsurance: hasLifeInsurance,
        riskTolerance: riskTolerance as 'low' | 'medium' | 'high',
      });
      setRecommendations(response.recommendations);
      setTotalCoverage(response.total_recommended_coverage);
      setTotalPremium(response.total_monthly_premium);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'life':
        return TbShield;
      case 'health':
        return TbHeartbeat;
      case 'disability':
        return TbUsers;
      default:
        return TbShield;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'life':
        return 'brand';
      case 'health':
        return 'accent';
      case 'disability':
        return 'blue';
      default:
        return 'gray';
    }
  };

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
              <Icon as={TbShield} boxSize={10} color={accentColor} />
              <Heading
                size="2xl"
                bgGradient={`linear(to-r, ${accentColor}, accent.500)`}
                bgClip="text"
                fontWeight="800"
              >
                Insurance Recommendations
              </Heading>
            </HStack>
            <Text fontSize="lg" color="text-secondary">
              Get personalized insurance recommendations based on your profile
            </Text>
          </VStack>
        </MotionBox>

        <Grid templateColumns={{ base: '1fr', lg: '1fr 2fr' }} gap={6}>
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
                <Heading size="md">Your Information</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <FormControl>
                    <FormLabel fontWeight="600">Age</FormLabel>
                    <Input
                      type="number"
                      value={age}
                      onChange={(e) => setAge(e.target.value)}
                      placeholder="Enter your age"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">Annual Income ($)</FormLabel>
                    <Input
                      type="number"
                      value={income}
                      onChange={(e) => setIncome(e.target.value)}
                      placeholder="Enter annual income"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">Number of Dependents</FormLabel>
                    <Input
                      type="number"
                      value={dependents}
                      onChange={(e) => setDependents(e.target.value)}
                      placeholder="0"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">Risk Tolerance</FormLabel>
                    <Select
                      value={riskTolerance}
                      onChange={(e) => setRiskTolerance(e.target.value)}
                    >
                      <option value="low">Low - Prefer maximum coverage</option>
                      <option value="medium">Medium - Balanced approach</option>
                      <option value="high">High - Minimal coverage</option>
                    </Select>
                  </FormControl>

                  <Divider />

                  <FormControl display="flex" alignItems="center" justifyContent="space-between">
                    <FormLabel mb={0} fontWeight="600">
                      Have Health Insurance?
                    </FormLabel>
                    <Switch
                      colorScheme="brand"
                      isChecked={hasHealthInsurance}
                      onChange={(e) => setHasHealthInsurance(e.target.checked)}
                    />
                  </FormControl>

                  <FormControl display="flex" alignItems="center" justifyContent="space-between">
                    <FormLabel mb={0} fontWeight="600">
                      Have Life Insurance?
                    </FormLabel>
                    <Switch
                      colorScheme="brand"
                      isChecked={hasLifeInsurance}
                      onChange={(e) => setHasLifeInsurance(e.target.checked)}
                    />
                  </FormControl>

                  <Button
                    onClick={getRecommendations}
                    isLoading={loading}
                    loadingText="Analyzing..."
                    colorScheme="brand"
                    size="lg"
                    fontWeight="700"
                    h={14}
                  >
                    Get Recommendations
                  </Button>

                  {recommendations.length > 0 && (
                    <MotionBox
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      p={4}
                      borderRadius="xl"
                      bg={summaryBg}
                    >
                      <VStack spacing={2} align="stretch">
                        <HStack justify="space-between">
                          <Text fontSize="sm" fontWeight="600" color="text-muted">
                            Total Coverage
                          </Text>
                          <Text fontSize="lg" fontWeight="700" color={accentColor}>
                            ${totalCoverage.toLocaleString()}
                          </Text>
                        </HStack>
                        <HStack justify="space-between">
                          <Text fontSize="sm" fontWeight="600" color="text-muted">
                            Monthly Premium
                          </Text>
                          <Text fontSize="lg" fontWeight="700" color={accentColor}>
                            ${totalPremium.toLocaleString()}
                          </Text>
                        </HStack>
                      </VStack>
                    </MotionBox>
                  )}
                </VStack>
              </CardBody>
            </MotionCard>
          </GridItem>

          {/* Recommendations Display */}
          <GridItem>
            <AnimatePresence>
              {recommendations.length === 0 ? (
                <MotionBox
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  h="full"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                >
                  <VStack spacing={4}>
                    <Icon as={TbShield} boxSize={20} color="text-muted" />
                    <Text fontSize="xl" color="text-muted" textAlign="center">
                      Fill in your information to get personalized recommendations
                    </Text>
                  </VStack>
                </MotionBox>
              ) : (
                <VStack spacing={4} align="stretch">
                  <Heading size="md">Recommended Plans</Heading>
                  <SimpleGrid columns={1} spacing={4}>
                    {recommendations.map((rec, index) => (
                      <MotionCard
                        key={rec.product.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4, delay: index * 0.1 }}
                        bg={cardBg}
                        borderWidth="2px"
                        borderColor={rec.score >= 80 ? accentColor : 'border-primary'}
                        shadow="xl"
                      >
                        <CardBody p={6}>
                          <VStack spacing={4} align="stretch">
                            <Flex justify="space-between" align="start">
                              <HStack spacing={3}>
                                <Icon
                                  as={getTypeIcon(rec.product.type)}
                                  boxSize={8}
                                  color={`${getTypeColor(rec.product.type)}.500`}
                                />
                                <VStack align="start" spacing={0}>
                                  <Heading size="md">{rec.product.name}</Heading>
                                  <Badge colorScheme={getTypeColor(rec.product.type)}>
                                    {rec.product.type}
                                  </Badge>
                                </VStack>
                              </HStack>
                              {rec.score >= 80 && (
                                <Badge colorScheme="brand" fontSize="md" px={3} py={1}>
                                  Top Pick
                                </Badge>
                              )}
                            </Flex>

                            <Text color="text-secondary">{rec.product.description}</Text>

                            <Box>
                              <Flex justify="space-between" mb={2}>
                                <Text fontSize="sm" fontWeight="600">
                                  Match Score
                                </Text>
                                <Text fontSize="sm" fontWeight="700" color={accentColor}>
                                  {rec.score}%
                                </Text>
                              </Flex>
                              <Progress
                                value={rec.score}
                                colorScheme="brand"
                                borderRadius="full"
                                size="sm"
                              />
                            </Box>

                            <Box
                              p={4}
                              borderRadius="lg"
                              bg={recommendationBg}
                            >
                              <Text fontSize="sm" color="text-secondary">
                                {rec.reason}
                              </Text>
                            </Box>

                            <Flex justify="space-between" align="center">
                              <VStack align="start" spacing={0}>
                                <Text fontSize="sm" color="text-muted">
                                  Monthly Premium
                                </Text>
                                <HStack spacing={1}>
                                  <Icon as={TbCoin} color="accent.500" />
                                  <Text fontSize="2xl" fontWeight="700" color={accentColor}>
                                    ${rec.product.monthly_premium}
                                  </Text>
                                </HStack>
                              </VStack>

                              <VStack align="end" spacing={0}>
                                <Text fontSize="sm" color="text-muted">
                                  Coverage
                                </Text>
                                <HStack spacing={1}>
                                  <Icon as={TbTrendingUp} color="brand.500" />
                                  <Text fontSize="2xl" fontWeight="700" color="brand.500">
                                    ${(rec.product.coverage_amount / 1000).toFixed(0)}K
                                  </Text>
                                </HStack>
                              </VStack>
                            </Flex>
                          </VStack>
                        </CardBody>
                      </MotionCard>
                    ))}
                  </SimpleGrid>
                </VStack>
              )}
            </AnimatePresence>
          </GridItem>
        </Grid>
      </Container>
    </Box>
  );
}
