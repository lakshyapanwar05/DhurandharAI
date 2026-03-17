import { useNetworkData } from './hooks/useNetworkData'
import Dashboard from './components/Dashboard'

function App() {
  const networkHook = useNetworkData()

  return <Dashboard {...networkHook} />
}

export default App
