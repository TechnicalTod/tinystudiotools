import unreal

@unreal.uclass()
class MyPIEExecutor(unreal.MoviePipelinePIEExecutor):
    def _post_init(self):
        super()._post_init()

    @unreal.ufunction(override=True)
    def execute(self, in_queue):
        unreal.log("Custom PIE Executor: Render (Local) button pressed.")
        #Manipulate the Queue Here
        
        
        # Call the original execute method to ensure the render process continues as normal.
        super().execute(in_queue)
