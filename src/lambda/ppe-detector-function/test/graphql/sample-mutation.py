"""
mutation newFrame {
  injestFrame(
    frame: {
        ppeResult: {
            summary: {
                sumPeopleWithRequiredEquipment: 0,
                sumPeopleWithoutRequiredEquipment: 1
            },
            personsWithoutRequiredEquipment: [
                {
                    id: 0,
                    missingMask: false,
                    missingHelmet: true
                    boundingBox: {
                        width: 0.432467520236969
                        height: 0.9722864031791687
                        left: 0.5623376369476318
                        top: 0.0
                    }
                }
            ],
            personsWithRequiredEquipment: []
        },
    camera: "test",
    s3url: "prod-frameprocessorstack-framebucket6a445548-1o2vm6nfi5pyq/test-laptop-1-2021-01-08-08:27:53:985000.jpg"
    ts: "1610094473985"
    }
  )
}
"""
