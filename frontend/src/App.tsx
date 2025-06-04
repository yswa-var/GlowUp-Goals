import { useState } from 'react'
import {
  Box,
  VStack,
  Input,
  Button,
  Text,
  useToast,
  Code,
  Flex,
  useColorModeValue,
} from '@chakra-ui/react'
import axios from 'axios'

function App() {
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const toast = useToast()
  
  const bgColor = useColorModeValue('gray.900', 'gray.900')
  const textColor = useColorModeValue('white', 'white')
  const inputBg = useColorModeValue('gray.800', 'gray.800')
  const codeBg = useColorModeValue('gray.800', 'gray.800')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    setIsLoading(true)
    try {
      const result = await axios.post('http://localhost:8000/chat', {
        message: message
      })
      
      if (result.data.error) {
        toast({
          title: 'Error',
          description: result.data.error,
          status: 'error',
          duration: 5000,
          isClosable: true,
        })
        setResponse({ error: result.data.error })
      } else {
        setResponse(result.data.response)
      }
      setMessage('')
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || 'Failed to get response from the server'
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
      setResponse({ error: errorMessage })
    } finally {
      setIsLoading(false)
    }
  }

  const renderResponse = () => {
    if (!response) return null

    if (response.error) {
      return (
        <Text color="red.400">
          Error: {response.error}
          {response.raw_response && (
            <Box mt={2}>
              <Text fontSize="sm" color="gray.400">Raw response:</Text>
              <Code p={2} mt={1} display="block" whiteSpace="pre-wrap" bg={codeBg} color={textColor}>
                {response.raw_response}
              </Code>
            </Box>
          )}
        </Text>
      )
    }

    return (
      <Code p={4} display="block" whiteSpace="pre-wrap" bg={codeBg} color={textColor}>
        {JSON.stringify(response, null, 2)}
      </Code>
    )
  }

  return (
    <Flex 
      direction="column" 
      h="100vh" 
      bg={bgColor}
      color={textColor}
    >
      <Box flex="1" overflowY="auto" p={4}>
        {renderResponse()}
      </Box>

      <Box 
        p={4} 
        borderTop="1px" 
        borderColor="gray.700"
        bg={bgColor}
      >
        <form onSubmit={handleSubmit}>
          <Flex gap={2}>
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask anything..."
              size="lg"
              bg={inputBg}
              color={textColor}
              _placeholder={{ color: 'gray.400' }}
              _hover={{ bg: 'gray.700' }}
              _focus={{ bg: 'gray.700' }}
              flex="1"
            />
            <Button
              type="submit"
              colorScheme="blue"
              isLoading={isLoading}
              loadingText="..."
              size="lg"
              px={8}
            >
              Send
            </Button>
          </Flex>
        </form>
      </Box>
    </Flex>
  )
}

export default App
