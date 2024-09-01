
import asyncio

DRIFT_UP = 1.25

class DeskHeight:

    async def run_task(self):        

        while True:
            self._abort = False
            if self._mode != DeskHeight.MODE_GOTO:
                await asyncio.sleep(0.5)
                continue
            
            height = self._get_average_height()
            if height < self._target_height:       
                # Move up         
                adj_target_height = self._target_height - DRIFT_UP                
                self._hardware.set_motors(True, False)
                while height < adj_target_height:
                    if self._abort:
                        break  # Back to the top of the WHILE
                    await asyncio.sleep(0.1)
                    height = self._hardware.get_height()
                self._hardware.set_motors(False, False)
                await asyncio.sleep(1)                
            else:   
                # Move down (same logic as move up)
                pass             

            self._mode = DeskHeight.MODE_IDLE
